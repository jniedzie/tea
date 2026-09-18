#!/usr/bin/env python3
"""Regression tests for scripts/format_python_tables.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("format_python_tables", ROOT / "scripts" / "format_python_tables.py")
assert SPEC and SPEC.loader
FORMATTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FORMATTER)


class FormatPythonTablesTest(unittest.TestCase):
  def test_splits_nested_expressions_without_splitting_nested_commas(self):
    self.assertEqual(
      FORMATTER.split_cells('"x,y", fn(1, 2), [3, 4]'),
      ['"x,y"', "fn(1, 2)", "[3, 4]"],
    )

  def test_aligns_tuple_rows_header_and_guards(self):
    source = """defaultHistParams = (
# collection  variable  bins  xmin  xmax  dir
    ("Event", "nMuon", 50, 0, 50, ""),
    ("Muon", "pt", 400, 0, 200, ""),
    ("Muon", "eta", 100, -2.5, 2.5, ""),
    ("NonGlobalMuons", "isGlobal", 2, -0.5, 1.5, ""),
)
"""
    expected = """# fmt: off
defaultHistParams = (
# collection        variable    bins  xmin  xmax  dir
    ("Event"         , "nMuon"   ,   50,    0,   50, ""),
    ("Muon"          , "pt"      ,  400,    0,  200, ""),
    ("Muon"          , "eta"     ,  100, -2.5,  2.5, ""),
    ("NonGlobalMuons", "isGlobal",    2, -0.5,  1.5, ""),
)
# fmt: on
"""
    formatted, count = FORMATTER.format_python_tables(source)
    self.assertEqual(formatted, expected)
    self.assertEqual(count, 1)

  def test_collapses_multiline_calls_and_optional_columns(self):
    source = """histograms = (
  # name  title  enabled  value  suffix
  Histogram("short", "", False, 1),
  Histogram(
    "a_very_long_name", "", True, 20, "_log"
  ),
  Histogram(
    "medium",
    "title, with comma",
    False,
    300,
  ),
)
"""
    expected = """# fmt: off
histograms = (
  # name                title                enabled  value  suffix
  Histogram("short"           , ""                 , False  ,     1),
  Histogram("a_very_long_name", ""                 , True   ,    20, "_log"),
  Histogram("medium"          , "title, with comma", False  ,   300),
)
# fmt: on
"""
    formatted, count = FORMATTER.format_python_tables(source)
    self.assertEqual(formatted, expected)
    self.assertEqual(count, 1)
    self.assertEqual(FORMATTER.format_python_tables(formatted)[0], formatted)

  def test_leaves_real_comments_and_mixed_call_names_untouched(self):
    source = """samples = (
  Sample(
    name="a",
    # This comment must remain on its own line.
    value=1,
  ),
  Sample(name="b", value=2),
)
mixed = (
  A("a", 1),
  B("b", 2),
)
"""
    self.assertEqual(FORMATTER.format_python_tables(source)[0], source)

  def test_does_not_turn_ordinary_repeated_calls_into_a_table(self):
    source = """samples = (
  Sample(
    name="DY",
    file_path="dy.root",
    cross_section=1976.0,
  ),
  Sample(
    name="tt",
    file_path="tt.root",
    cross_section=687.1,
  ),
)
"""
    self.assertEqual(FORMATTER.format_python_tables(source)[0], source)

  def test_ignores_table_shaped_text_inside_multiline_strings(self):
    source = '''example = """x = (
  # left  right
  ("a", 1),
  ("long", 20),
)
"""
'''
    self.assertEqual(FORMATTER.format_python_tables(source)[0], source)

  def test_check_mode_reports_drift_without_writing(self):
    source = 'x = (\n  # left  right\n  ("a", 1),\n  ("long", 20),\n)\n'
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "config.py"
      path.write_text(source)
      self.assertEqual(FORMATTER.main(["--check", str(path)]), 1)
      self.assertEqual(path.read_text(), source)
      self.assertEqual(FORMATTER.main([str(path)]), 0)
      self.assertEqual(FORMATTER.main(["--check", str(path)]), 0)


if __name__ == "__main__":
  unittest.main()
