import re
import inspect
import socket
import os
from pathlib import Path
import sys
from Logger import error, warn


def ensure_root_compiler_environment():
  """Restore the Conda compiler sysroot for partially activated Linux shells.

  ROOT's interpreter needs system headers even when executing a compiled app.
  Set this before importing ROOT, and inherit it in submitted local children.
  Explicit compiler settings and non-Conda ROOT installations are untouched.
  """
  if sys.platform != "linux" or os.environ.get("CONDA_BUILD_SYSROOT"):
    return
  prefix = Path(os.environ.get("ROOTSYS") or os.environ.get("CONDA_PREFIX") or sys.prefix)
  sysroot = prefix / "x86_64-conda-linux-gnu/sysroot"
  if (prefix / "conda-meta").is_dir() and (sysroot / "usr/include/assert.h").is_file():
    os.environ["CONDA_BUILD_SYSROOT"] = str(sysroot)
    warn(f"Restored ROOT compiler sysroot: {sysroot}. Source tea/setup.sh for the full environment.")


def get_year_from_samples(samples):
  frame = inspect.currentframe().f_back
  ns = frame.f_globals.copy()
  ns.update(frame.f_locals)

  source_name = None
  for name, obj in list(ns.items()):  # snapshot with list(...)
    if isinstance(obj, dict) and obj.keys() == samples:  # same keys view
      source_name = name
      break

  if not source_name:
    error("Could not find the year in the sample variable.")
    return None

  m = re.search(r"(\d{4}[A-Za-z]*)", source_name)
  return m.group(1) if m else None


def get_facility():
  hostname = socket.gethostname()
  if "lxplus" in hostname:
    facility = "lxplus"
  elif "naf" in hostname:
    facility = "naf"
  elif "iihe.ac.be" in hostname:
    facility = "vub"
  else:
    warn(f"Unknown facility for hostname: {hostname}, defaulting to generic template")
    facility = "default"

  return facility
