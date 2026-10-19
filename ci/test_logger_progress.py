"""Progress stays visible without hiding diagnostics or claiming unfinished work."""

from contextlib import redirect_stdout
from io import StringIO
from os import terminal_size
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pylibs" / "logger"))
import Logger


class CapturedOutput(StringIO):
  def __init__(self, terminal=False):
    super().__init__()
    self.terminal = terminal
    self.flushes = 0

  def isatty(self):
    return self.terminal

  def flush(self):
    self.flushes += 1


class LoggerProgressTest(unittest.TestCase):
  def test_redirected_multiline_frame_is_readable_and_flushed(self):
    output = CapturedOutput()
    with redirect_stdout(output):
      Logger.info_frame("Plots were saved to:\n/project/plots/study")
    lines = output.getvalue().splitlines()
    self.assertEqual(len(lines), 4)
    self.assertIn("│ Plots were saved to:", lines[1])
    self.assertIn("│ /project/plots/study", lines[2])
    self.assertEqual(len({len(line) for line in lines}), 1)
    self.assertNotIn("\033", output.getvalue())
    self.assertGreater(output.flushes, 0)

  def test_terminal_frame_wraps_paths_and_redraws_progress(self):
    output = CapturedOutput(terminal=True)
    path = "/project/plots/a directory/" + "long_path_" * 10
    with (
      redirect_stdout(output),
      patch.object(Logger.shutil, "get_terminal_size", return_value=terminal_size((60, 24))),
    ):
      with Logger.ProgressBar(3, label="Items") as progress:
        progress.update(1)
        Logger.info_frame("Plots were saved to:\n" + path)
    text = output.getvalue()
    frame_start = text.index("╭")
    frame_end = text.index("╯", frame_start) + 1
    frame_lines = text[frame_start:frame_end].splitlines()
    self.assertTrue(all(len(line) < 60 for line in frame_lines))
    path_lines = frame_lines[2:-1]
    self.assertEqual("".join(line[2:-2].rstrip() for line in path_lines), path)
    self.assertIn("\033[1;92m╭", text)
    self.assertIn("33% (Items 1/3)", text[frame_end:])
    self.assertIn("\n\r\033[2K\033[1;92m[", text[frame_end:])

  def test_redirected_progress_flushes_and_throttles_intermediate_updates(self):
    output = CapturedOutput()
    with redirect_stdout(output), patch.object(Logger.time, "monotonic", return_value=10) as clock:
      with Logger.ProgressBar(3, label="Items") as progress:
        self.assertGreater(output.flushes, 0)
        progress.update(1)
        clock.return_value = 10.3
        progress.update(2)
        progress.update(3)
    lines = output.getvalue().splitlines()
    self.assertEqual(len(lines), 3)
    self.assertIn("0% (Items 0/3)", lines[0])
    self.assertIn("66% (Items 2/3)", lines[1])
    self.assertIn("100% (Items 3/3)", lines[2])
    self.assertNotIn("\033", output.getvalue())
    self.assertGreaterEqual(output.flushes, 3)
    self.assertIsNone(Logger.active_progress_bar)

  def test_exception_keeps_the_completed_count_and_propagates(self):
    output = CapturedOutput()
    with redirect_stdout(output):
      with self.assertRaisesRegex(RuntimeError, "Expected error"):
        with Logger.ProgressBar(3, label="Items") as progress:
          progress.update(1)
          raise RuntimeError("Expected error")
    self.assertIn("33% (Items 1/3)", output.getvalue())
    self.assertIn("Interrupted", output.getvalue())
    self.assertNotIn("100%", output.getvalue())
    self.assertIsNone(Logger.active_progress_bar)

  def test_iterator_completion_and_early_close_report_actual_counts(self):
    output = CapturedOutput()
    with redirect_stdout(output):
      self.assertEqual(list(Logger.ProgressBar.iterate([1, 2, 3], label="Items")), [1, 2, 3])
    self.assertIn("100% (Items 3/3)", output.getvalue())
    output = CapturedOutput()
    with redirect_stdout(output):
      items = Logger.ProgressBar.iterate([1, 2, 3], label="Items")
      self.assertEqual(next(items), 1)
      self.assertEqual(next(items), 2)
      items.close()
    self.assertIn("33% (Items 1/3)", output.getvalue())
    self.assertNotIn("100%", output.getvalue())
    self.assertIsNone(Logger.active_progress_bar)

  def test_terminal_warning_is_printed_before_the_bar_is_redrawn(self):
    output = CapturedOutput(terminal=True)
    with redirect_stdout(output), patch.dict(Logger.warn_messages, {}, clear=True):
      with Logger.ProgressBar(3, label="Items") as progress:
        progress.update(1)
        Logger.warn("Visible warning")
    text = output.getvalue()
    warning_index = text.index("Visible warning")
    self.assertIn("\n\r\033[2K\033[1;92m[", text[warning_index:])
    self.assertIn("33% (Items 1/3)", text[warning_index:])
    self.assertTrue(text.endswith("\n"))
    self.assertGreaterEqual(output.flushes, 4)

  def test_terminal_progress_fits_the_width_and_keeps_counts(self):
    for columns in (60, 80, 120):
      with self.subTest(columns=columns):
        output = CapturedOutput(terminal=True)
        with (
          redirect_stdout(output),
          patch.object(Logger.shutil, "get_terminal_size", return_value=terminal_size((columns, 24))),
        ):
          with Logger.ProgressBar(100, label="Loading histograms", interval=0) as progress:
            progress.update(40, "A sample with a very long histogram name " * 4)
        text = re.sub(r"\033\[[0-9;]*[A-Za-z]", "", output.getvalue())
        lines = [line for line in text.split("\r") if line.strip()]
        self.assertTrue(all(len(line.rstrip("\n")) < columns for line in lines))
        self.assertIn("40% (Loading histograms 40/100)", text)
        self.assertIn("...", text)


if __name__ == "__main__":
  unittest.main()
