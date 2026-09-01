#!/usr/bin/env python3

"""Publish a relocated conda environment with bounded parallel copies."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def copy_entry(source: Path, destination: Path) -> None:
  if source.is_symlink():
    destination.symlink_to(os.readlink(source))
    return
  if source.is_file():
    source_stat = source.stat()
    shutil.copyfile(source, destination, follow_symlinks=False)
    os.chmod(destination, stat.S_IMODE(source_stat.st_mode))
    return
  raise RuntimeError(f"unsupported environment entry: {source}")


def copy_directory_metadata(source: Path, destination: Path) -> None:
  source_stat = source.stat()
  os.chmod(destination, stat.S_IMODE(source_stat.st_mode))


def publish(source: Path, destination: Path, workers: int) -> int:
  source = source.resolve(strict=True)
  destination = destination.absolute()
  if destination.exists() or destination.is_symlink():
    raise RuntimeError(f"publication destination already exists: {destination}")
  if source == destination or source in destination.parents:
    raise RuntimeError("publication destination must not be inside the source")

  directories: list[tuple[Path, Path]] = []
  entries: list[tuple[Path, Path]] = []
  for root, directory_names, file_names in os.walk(source, followlinks=False):
    source_root = Path(root)
    relative_root = source_root.relative_to(source)
    destination_root = destination / relative_root
    directories.append((source_root, destination_root))
    for name in directory_names:
      candidate = source_root / name
      if candidate.is_symlink():
        entries.append((candidate, destination_root / name))
    directory_names[:] = [name for name in directory_names if not (source_root / name).is_symlink()]
    entries.extend((source_root / name, destination_root / name) for name in file_names)

  for _, destination_directory in directories:
    destination_directory.mkdir(parents=True, exist_ok=False)

  print(
    f"tea: publishing {len(entries)} files with {workers} parallel workers",
    file=sys.stderr,
  )
  with ThreadPoolExecutor(max_workers=workers) as executor:
    futures = [executor.submit(copy_entry, *pair) for pair in entries]
    for completed, future in enumerate(as_completed(futures), start=1):
      future.result()
      if completed % 5000 == 0:
        print(f"tea: published {completed}/{len(entries)} files", file=sys.stderr)

  # Apply directory permissions after all entries are present. Timestamps and
  # extended attributes are not required by conda and are expensive remotely.
  with ThreadPoolExecutor(max_workers=workers) as executor:
    list(executor.map(lambda pair: copy_directory_metadata(*pair), directories))
  return len(entries)


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("source", type=Path)
  parser.add_argument("destination", type=Path)
  parser.add_argument("--workers", type=int, default=32)
  arguments = parser.parse_args()
  if arguments.workers < 1 or arguments.workers > 32:
    parser.error("--workers must be between 1 and 32")

  try:
    count = publish(arguments.source, arguments.destination, arguments.workers)
  except Exception as error:  # noqa: BLE001 - keep command-line failures concise
    print(f"tea: environment publication failed: {error}", file=sys.stderr)
    return 1
  print(f"tea: published {count} files", file=sys.stderr)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
