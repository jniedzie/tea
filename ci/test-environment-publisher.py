#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
from pathlib import Path

framework = Path(__file__).resolve().parents[1]
publisher_path = framework / "environment" / "publish_environment.py"
spec = importlib.util.spec_from_file_location("tea_environment_publisher", publisher_path)
assert spec is not None and spec.loader is not None
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

with tempfile.TemporaryDirectory() as temporary:
  root = Path(temporary)
  source = root / "source"
  destination = root / "destination"
  (source / "bin").mkdir(parents=True)
  (source / "empty").mkdir()
  tool = source / "bin" / "tool"
  tool.write_text("#!/bin/sh\n", encoding="utf-8")
  tool.chmod(0o755)
  (source / "tool-link").symlink_to("bin/tool")

  assert publisher.publish(source, destination, workers=2) == 2
  assert (destination / "empty").is_dir()
  assert os.readlink(destination / "tool-link") == "bin/tool"
  assert stat.S_IMODE((destination / "bin" / "tool").stat().st_mode) == 0o755
  assert (destination / "bin" / "tool").read_text(encoding="utf-8") == "#!/bin/sh\n"

print("tea environment publisher check passed")
