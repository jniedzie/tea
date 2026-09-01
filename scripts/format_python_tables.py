#!/usr/bin/env python3
"""Align consecutive tuple/call rows that form tables in Python files.

The formatter also wraps the containing assignment in ``# fmt: off/on`` so
Ruff preserves the alignment.  Run without options to update files in place;
use ``--check`` in CI to report formatting drift without changing files.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import io
from pathlib import Path
import re
import sys
import tokenize


NUMERIC = re.compile(
  r"^[+-]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|0[xob][0-9a-f]+)$",
  re.IGNORECASE,
)
ROW_START = re.compile(r"^(\s*)((?:[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)?)\((.*)$")
FMT_OFF = re.compile(r"^\s*#\s*fmt:\s*off\s*$")
FMT_ON = re.compile(r"^\s*#\s*fmt:\s*on\s*$")


def split_cells(text: str) -> list[str] | None:
  cells: list[str] = []
  start = 0
  depth = 0
  quote: str | None = None
  escaped = False

  for index, char in enumerate(text):
    if quote:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
      continue
    if char in {'"', "'"}:
      quote = char
    elif char in "([{":
      depth += 1
    elif char in ")]}":
      depth -= 1
      if depth < 0:
        return None
    elif char == "," and depth == 0:
      cells.append(text[start:index].strip())
      start = index + 1

  if quote or depth != 0:
    return None
  final_cell = text[start:].strip()
  if final_cell:
    cells.append(final_cell)
  if len(cells) < 2 or not all(cells):
    return None
  return cells


def has_padded_separator(text: str) -> bool:
  """Return whether a one-line row already has table-like padding before a comma."""
  if "\n" in text:
    return False
  depth = 0
  quote: str | None = None
  escaped = False
  cell_start = 0
  for index, char in enumerate(text):
    if quote:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
      continue
    if char in {'"', "'"}:
      quote = char
    elif char in "([{":
      depth += 1
    elif char in ")]}":
      depth -= 1
    elif char == "," and depth == 0:
      raw_cell = text[cell_start:index]
      if raw_cell.rstrip() != raw_cell:
        return True
      cell_start = index + 1
  return False


def matching_close(text: str, opening: int) -> int:
  pairs = {"(": ")", "[": "]", "{": "}"}
  stack: list[str] = []
  quote: str | None = None
  escaped = False
  comment = False

  for index in range(opening, len(text)):
    char = text[index]
    if comment:
      if char == "\n":
        comment = False
      continue
    if quote:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
      continue
    if char == "#":
      comment = True
    elif char in {'"', "'"}:
      quote = char
    elif char in pairs:
      stack.append(pairs[char])
    elif char in ")]}":
      if not stack or stack.pop() != char:
        return -1
      if not stack:
        return index
  return -1


def collapse_whitespace(text: str) -> str:
  result: list[str] = []
  quote: str | None = None
  escaped = False
  pending_space = False

  for char in text.strip():
    if quote:
      result.append(char)
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
    elif char in {'"', "'"}:
      if pending_space and result and result[-1] != " ":
        result.append(" ")
      pending_space = False
      quote = char
      result.append(char)
    elif char.isspace():
      pending_space = True
    else:
      if pending_space and result and result[-1] != " ":
        result.append(" ")
      pending_space = False
      result.append(char)
  return "".join(result)


def has_comment_outside_string(text: str) -> bool:
  quote: str | None = None
  escaped = False
  for char in text:
    if quote:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
    elif char in {'"', "'"}:
      quote = char
    elif char == "#":
      return True
  return False


def parse_logical_row(lines: list[str], first: int) -> dict[str, object] | None:
  match = ROW_START.match(lines[first])
  if not match:
    return None
  opening = len(match.group(1)) + len(match.group(2))

  for last in range(first, min(len(lines), first + 200)):
    text = "\n".join(lines[first : last + 1])
    if '"""' in text or "'''" in text:
      return None
    closing = matching_close(text, opening)
    if closing < 0:
      continue
    if text[closing + 1 :].strip() != ",":
      return None
    contents = text[opening + 1 : closing]
    if has_comment_outside_string(contents):
      return None
    cells = split_cells(contents)
    if not cells:
      return None
    return {
      "first": first,
      "last": last,
      "indent": match.group(1),
      "opener": match.group(2),
      "cells": [collapse_whitespace(cell) for cell in cells],
      "padded": has_padded_separator(contents),
    }
  return None


def code_for_brackets(line: str) -> str:
  result: list[str] = []
  quote: str | None = None
  escaped = False
  for char in line:
    if quote:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == quote:
        quote = None
      result.append(" ")
    elif char == "#":
      break
    elif char in {'"', "'"}:
      quote = char
      result.append(" ")
    else:
      result.append(char)
  return "".join(result)


def bracket_delta(line: str) -> int:
  code = code_for_brackets(line)
  return sum(char in "([{" for char in code) - sum(char in ")] }".replace(" ", "") for char in code)


def enclosing_statement(lines: list[str], first_row: int, last_row: int) -> tuple[int, int] | None:
  for start in range(first_row - 1, max(-1, first_row - 81), -1):
    if "=" not in lines[start]:
      continue
    balance = sum(bracket_delta(lines[index]) for index in range(start, last_row + 1))
    if balance <= 0:
      continue
    for end in range(last_row + 1, len(lines)):
      balance += bracket_delta(lines[end])
      if balance == 0:
        return start, end
      if balance < 0:
        break
  return None


def header_labels(line: str, arity: int) -> tuple[str, list[str]] | None:
  match = re.match(r"^(\s*)#\s*(.*?)\s*$", line)
  if not match:
    return None
  labels = [label.removesuffix(",") for label in match.group(2).strip().split()]
  return (match.group(1), labels) if len(labels) == arity else None


def align_group(lines: list[str], group: dict[str, object], align_header: bool) -> int:
  rows = group["rows"]
  assert isinstance(rows, list)
  arity = max(len(row["cells"]) for row in rows)
  first = int(group["first"])
  header = header_labels(lines[first - 1], arity) if align_header and first > 0 else None
  widths: list[int] = []
  numeric: list[bool] = []

  for column in range(arity):
    values = [row["cells"][column] for row in rows if column < len(row["cells"])]
    lengths = [len(value) for value in values]
    if header and column < arity - 1:
      lengths.append(len(header[1][column]))
    widths.append(max(lengths))
    numeric.append(all(NUMERIC.fullmatch(value) for value in values))

  removed_lines = 0
  for row in reversed(rows):
    rendered = [
      cell.rjust(widths[column]) if numeric[column] else cell.ljust(widths[column])
      for column, cell in enumerate(row["cells"])
    ]
    first_line = int(row["first"])
    last_line = int(row["last"])
    lines[first_line : last_line + 1] = [f"{row['indent']}{row['opener']}({', '.join(rendered)}),"]
    removed_lines += last_line - first_line

  if header:
    fields = [label.ljust(widths[column]) for column, label in enumerate(header[1])]
    lines[first - 1] = f"{header[0]}# {'  '.join(fields).rstrip()}"
  return removed_lines


def multiline_string_lines(source: str) -> set[int]:
  blocked: set[int] = set()
  try:
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for token in tokens:
      if token.type == tokenize.STRING and token.start[0] != token.end[0]:
        blocked.update(range(token.start[0] - 1, token.end[0]))
  except (IndentationError, SyntaxError, tokenize.TokenError):
    # The normal CLI syntax check reports invalid Python. Keeping this helper
    # conservative avoids making its own parsing failure destructive.
    return set(range(len(source.splitlines())))
  return blocked


def find_groups(lines: list[str], minimum_rows: int, blocked_lines: set[int]) -> list[dict[str, object]]:
  groups: list[dict[str, object]] = []
  index = 0
  while index < len(lines):
    if index in blocked_lines:
      index += 1
      continue
    first = parse_logical_row(lines, index)
    if not first:
      index += 1
      continue
    rows = [first]
    end = int(first["last"]) + 1
    while end < len(lines):
      if end in blocked_lines:
        break
      row = parse_logical_row(lines, end)
      if not row or row["indent"] != first["indent"] or row["opener"] != first["opener"]:
        break
      rows.append(row)
      end = int(row["last"]) + 1
    if len(rows) >= minimum_rows:
      groups.append({"first": index, "last": rows[-1]["last"], "rows": rows})
    index = end
  return groups


def active_fmt_off(lines: list[str], before: int) -> bool:
  off = False
  for line in lines[:before]:
    if FMT_OFF.match(line):
      off = True
    elif FMT_ON.match(line):
      off = False
  return off


def group_has_header(lines: list[str], group: dict[str, object]) -> bool:
  first = int(group["first"])
  if first == 0:
    return False
  rows = group["rows"]
  assert isinstance(rows, list)
  arity = max(len(row["cells"]) for row in rows)
  return header_labels(lines[first - 1], arity) is not None


def format_python_tables(
  source: str,
  *,
  minimum_rows: int = 2,
  align_header_comment: bool = True,
  insert_fmt_guards: bool = True,
) -> tuple[str, int]:
  newline = "\r\n" if "\r\n" in source else "\n"
  had_final_newline = source.endswith("\n")
  lines = source.splitlines()
  groups = find_groups(lines, minimum_rows, multiline_string_lines(source))
  statements: list[dict[str, object]] = []

  for group in groups:
    statement = enclosing_statement(lines, int(group["first"]), int(group["last"]))
    if not statement:
      continue
    rows = group["rows"]
    assert isinstance(rows, list)
    looks_like_table = (
      active_fmt_off(lines, statement[0]) or group_has_header(lines, group) or any(bool(row["padded"]) for row in rows)
    )
    if not looks_like_table:
      continue
    item = next(
      (candidate for candidate in statements if (candidate["start"], candidate["end"]) == statement),
      None,
    )
    if item is None:
      item = {"start": statement[0], "end": statement[1], "groups": []}
      statements.append(item)
    item["groups"].append(group)

  for statement in sorted(statements, key=lambda item: int(item["start"]), reverse=True):
    removed_lines = 0
    for group in sorted(statement["groups"], key=lambda item: int(item["first"]), reverse=True):
      removed_lines += align_group(lines, group, align_header_comment)
    start = int(statement["start"])
    if insert_fmt_guards and not active_fmt_off(lines, start):
      indent = re.match(r"^\s*", lines[start]).group(0)
      lines.insert(int(statement["end"]) - removed_lines + 1, f"{indent}# fmt: on")
      lines.insert(start, f"{indent}# fmt: off")

  result = newline.join(lines) + (newline if had_final_newline else "")
  return result, len(statements)


def read_source(path: Path) -> tuple[str, str]:
  data = path.read_bytes()
  encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
  return data.decode(encoding), encoding


def process_file(path: Path, *, check: bool, show_diff: bool) -> bool:
  source, encoding = read_source(path)
  formatted, _ = format_python_tables(source)
  if formatted == source:
    return False

  ast.parse(formatted, filename=str(path))
  if show_diff:
    sys.stdout.writelines(
      difflib.unified_diff(
        source.splitlines(keepends=True),
        formatted.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
      )
    )
  if check:
    print(f"Would reformat: {path}")
  else:
    path.write_bytes(formatted.encode(encoding))
    print(f"Reformatted: {path}")
  return True


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--check", action="store_true", help="report drift without changing files")
  parser.add_argument("--diff", action="store_true", help="show the proposed unified diff")
  parser.add_argument("files", nargs="*", type=Path)
  args = parser.parse_args(argv)

  changed = False
  failed = False
  for path in args.files:
    if path.suffix != ".py" or not path.is_file():
      continue
    try:
      changed |= process_file(path, check=args.check, show_diff=args.diff)
    except (OSError, SyntaxError, UnicodeError, tokenize.TokenError) as error:
      failed = True
      print(f"Could not format {path}: {error}", file=sys.stderr)
  return 1 if failed or (args.check and changed) else 0


if __name__ == "__main__":
  raise SystemExit(main())
