import shutil
import sys
import time


warn_messages = {}
error_messages = {}
fatal_messages = {}
root_warning_collector_installed = False
active_progress_bar = None


class ProgressBar:
  """Show tea-style progress without printing on every loop iteration."""

  def __init__(self, total, label="Progress", interval=0.2, width=50):
    self.total = max(0, total)
    self.label = label
    self.interval = interval
    self.width = width
    self.current = 0
    self.detail = ""
    self.last_update = 0
    self.last_rendered_current = None

  def __enter__(self):
    global active_progress_bar
    self.previous_progress_bar = active_progress_bar
    active_progress_bar = self
    self.is_terminal = sys.stdout.isatty()
    self.start_time = time.monotonic()
    self._render(force=True)
    return self

  def update(self, current, detail=""):
    self.current = max(0, min(self.total, current))
    self.detail = detail
    self._render(force=self.current == self.total)

  @classmethod
  def iterate(cls, items, label="Progress"):
    with cls(len(items), label=label) as progress:
      for index, item in enumerate(items):
        detail = item.getName() if hasattr(item, "getName") else getattr(item, "name", "")
        progress.update(index, detail)
        yield item
        progress.update(index + 1, detail)

  def _render(self, force=False):
    now = time.monotonic()
    if not force and now - self.last_update < self.interval:
      return
    self.last_update = now
    self.last_rendered_current = self.current
    percentage = self.current * 100 // self.total if self.total else 100
    elapsed = int(now - self.start_time)
    width = self.width
    label = self.label
    if self.is_terminal:
      # Leave one column unused so a full progress line does not wrap.
      columns = shutil.get_terminal_size().columns - 1
      counter_width = len(f"[] {percentage}% ( {self.current}/{self.total}) | {elapsed}s")
      label = label[: max(0, columns - counter_width - 5)]
    suffix = f" {percentage}% ({label} {self.current}/{self.total}) | {elapsed}s"
    if self.is_terminal:
      available = columns - len(suffix) - 2
      detail_width = min(24, max(0, available - 5)) if self.detail else 0
      width = max(1, min(width, available - detail_width))
    position = percentage * width // 100
    bar = "=" * position
    if position < width:
      bar += ">" + " " * (width - position - 1)
    line = f"[{bar}]{suffix}"
    if self.detail:
      detail = self.detail
      if self.is_terminal:
        available = max(0, columns - len(line) - 3)
        if len(detail) > available:
          detail = detail[: max(0, available - 3)] + ("..." if available >= 3 else "")
      if detail:
        line += f" | {detail}"
    if self.is_terminal:
      print(f"\r\033[2K\033[1;92m{line}\033[0m", end="", flush=True)
    else:
      print(line, flush=True)

  def __exit__(self, exception_type, exception, traceback):
    global active_progress_bar
    if exception_type is None:
      if self.last_rendered_current != self.current:
        self._render(force=True)
    else:
      self.detail = "Interrupted"
      self._render(force=True)
    if self.is_terminal:
      print(flush=True)
    active_progress_bar = self.previous_progress_bar
    return False


def _print_message(message, end="\n"):
  progress = active_progress_bar
  if progress is not None and progress.is_terminal:
    print("\r\033[2K", end="")
  print(message, end=end, flush=True)
  if progress is not None and progress.is_terminal:
    progress._render(force=True)


def info(message, end="\n"):
  _print_message(message, end=end)


def info_frame(message):
  """Highlight a multiline message without losing long paths to truncation."""
  max_width = max(1, shutil.get_terminal_size().columns - 5)
  lines = []
  for line in str(message).splitlines() or [""]:
    # Wrap without stripping spaces, which can be part of a file path.
    lines.extend(line[index : index + max_width] for index in range(0, len(line), max_width))
    if not line:
      lines.append("")
  width = max(len(line) for line in lines)
  frame = ["╭" + "─" * (width + 2) + "╮"]
  frame.extend(f"│ {line.ljust(width)} │" for line in lines)
  frame.append("╰" + "─" * (width + 2) + "╯")
  text = "\n".join(frame)
  if sys.stdout.isatty():
    text = f"\033[1;92m{text}\033[0m"
  _print_message(text)


def warn(message):
  if message in warn_messages:
    warn_messages[message] += 1
    return

  warn_messages[message] = 1
  _print_message(f"[first occurance]\033[1;33m{message}\033[0m")


def install_root_warning_collector():
  """Collect selected noisy ROOT warnings for the final logger summary."""
  import ROOT

  global root_warning_collector_installed
  if root_warning_collector_installed:
    return

  ROOT.gInterpreter.Declare(r"""
    #ifndef TEA_ROOT_WARNING_COLLECTOR
    #define TEA_ROOT_WARNING_COLLECTOR
    #include <cstring>
    #include "TError.h"

    namespace TeaRootWarnings {
      unsigned long empty_histogram_count = 0;
      unsigned long non_exact_rebin_count = 0;
      ErrorHandlerFunc_t previous_handler = nullptr;
      bool installed = false;

      void Handle(int level, Bool_t abort, const char *location,
                  const char *message) {
        if (location && message && std::strcmp(location, "TH1::TH1") == 0 &&
            std::strstr(message, "nbins is <=0")) {
          ++empty_histogram_count;
          return;
        }

        if (location && message && std::strstr(location, "::Rebin") &&
            std::strstr(message, "is not an exact divider of nbins=")) {
          ++non_exact_rebin_count;
          return;
        }

        if (previous_handler)
          previous_handler(level, abort, location, message);
        else
          DefaultErrorHandler(level, abort, location, message);
      }

      void Install() {
        if (installed)
          return;
        previous_handler = SetErrorHandler(Handle);
        installed = true;
      }

      unsigned long TakeEmptyHistogramCount() {
        const auto count = empty_histogram_count;
        empty_histogram_count = 0;
        return count;
      }

      unsigned long TakeNonExactRebinCount() {
        const auto count = non_exact_rebin_count;
        non_exact_rebin_count = 0;
        return count;
      }
    }
    #endif
  """)
  ROOT.TeaRootWarnings.Install()
  root_warning_collector_installed = True


def collect_root_warnings():
  if not root_warning_collector_installed:
    return

  import ROOT

  empty_count = int(ROOT.TeaRootWarnings.TakeEmptyHistogramCount())
  rebin_count = int(ROOT.TeaRootWarnings.TakeNonExactRebinCount())

  empty_message = "ROOT encountered an empty histogram (nbins <= 0; using one bin)."
  rebin_message = "ROOT rebinning group is not an exact divider of the histogram bins."
  warn_messages[empty_message] = warn_messages.get(empty_message, 0) + empty_count
  warn_messages[rebin_message] = warn_messages.get(rebin_message, 0) + rebin_count

  if warn_messages[empty_message] == 0:
    del warn_messages[empty_message]
  if warn_messages[rebin_message] == 0:
    del warn_messages[rebin_message]


def error(message):
  if message in error_messages:
    error_messages[message] += 1
    return

  error_messages[message] = 1

  _print_message(f"[first occurance]\033[1;31m{message}\033[0m")


def fatal(message):
  if message in fatal_messages:
    fatal_messages[message] += 1
    return

  fatal_messages[message] = 1

  _print_message("[first occurance]\033[1;35m" + message + "\033[0m")


def logger_print():
  collect_root_warnings()

  for message, count in warn_messages.items():
    print(f"[occured {count} times]\033[1;33m{message}\033[0m")

  for message, count in error_messages.items():
    print(f"[occured {count} times]\033[1;31m{message}\033[0m")

  for message, count in fatal_messages.items():
    print(f"[occured {count} times]\033[1;35m{message}\033[0m")
