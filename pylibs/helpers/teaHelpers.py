import re
import inspect
import math
import os
import random
import shutil
import socket
import subprocess
import threading
import time
from Logger import error, info, warn


ROOT_VALIDATION_LOCK = threading.Lock()

GFAL_DOOR = "davs://maite.iihe.ac.be:2880"
DCACHE_LOCAL_PREFIX = "/dcache_mnt/dcache"
GFAL_COPY_TIMEOUT_SECONDS = 600
GFAL_COPY_MAX_ATTEMPTS = 5
GFAL_COPY_RETRY_BASE_WAIT_SECONDS = 20
GFAL_COPY_RETRY_EXPO_HALF_LIFE_SECONDS = 60


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


def validate_root_file(file_path):
  import ROOT

  with ROOT_VALIDATION_LOCK:
    previous_error_level = ROOT.gErrorIgnoreLevel
    ROOT.gErrorIgnoreLevel = ROOT.kFatal
    try:
      root_file = ROOT.TFile.Open(file_path, "READ")
      if not root_file or root_file.IsZombie() or root_file.GetNkeys() == 0:
        if root_file:
          root_file.Close()
        raise RuntimeError(f"ROOT file is invalid or contains no keys: {file_path}")
      root_file.Close()
    finally:
      ROOT.gErrorIgnoreLevel = previous_error_level


def _dcache_gfal_url(final_path):
  # final_path is typically a symlink into pnfs (e.g. results/results-unmerged ->
  # /pnfs/iihe/...); realpath resolves both the symlink and dCache's local mount
  # prefix, neither of which the davs door accepts directly.
  real_path = os.path.normpath(os.path.realpath(final_path))
  if real_path.startswith(DCACHE_LOCAL_PREFIX + "/pnfs/"):
    real_path = real_path[len(DCACHE_LOCAL_PREFIX) :]
  if not real_path.startswith("/pnfs/"):
    return None
  return GFAL_DOOR + real_path


def _run_gfal_copy(local_path, dest_url):
  # -f: dCache is write-once, so a resubmit's overwrite needs -f to replace the
  # existing destination file rather than failing with "File exists".
  return subprocess.run(
    [
      "gfal-copy",
      "-f",
      "-p",
      "-t",
      str(GFAL_COPY_TIMEOUT_SECONDS),
      "--checksum",
      "ADLER32",
      f"file://{os.path.abspath(local_path)}",
      dest_url,
    ],
    check=False,
    capture_output=True,
    text=True,
  )


def _stage_local_copy(local_path, final_path):
  os.makedirs(os.path.dirname(os.path.abspath(final_path)), exist_ok=True)
  shutil.copyfile(local_path, final_path)


def _stage_vub_gfal(local_path, final_path):
  dest_url = _dcache_gfal_url(final_path)
  if dest_url is None:
    info(f"{final_path} does not resolve to a pnfs path; copying directly instead of using gfal-copy")
    _stage_local_copy(local_path, final_path)
    return

  last_exception = None
  for attempt in range(1, GFAL_COPY_MAX_ATTEMPTS + 1):
    result = _run_gfal_copy(local_path, dest_url)
    if result.returncode == 0:
      return

    last_exception = RuntimeError(
      f"gfal-copy failed (exit {result.returncode}) staging {local_path} -> {dest_url}: "
      f"stdout={result.stdout.strip()!r} stderr={result.stderr.strip()!r}"
    )

    if attempt < GFAL_COPY_MAX_ATTEMPTS:
      # Constant GFAL_COPY_RETRY_BASE_WAIT_SECONDS (20 s) plus a random exponential
      # jitter with a 1-minute half-life (median wait ~80 s, mean ~107 s), so concurrent
      # retries from ~1500 jobs don't all hammer the door at the same instant (a plain
      # fixed backoff would).
      wait_seconds = GFAL_COPY_RETRY_BASE_WAIT_SECONDS + random.expovariate(
        math.log(2) / GFAL_COPY_RETRY_EXPO_HALF_LIFE_SECONDS
      )
      warn(
        f"gfal-copy attempt {attempt}/{GFAL_COPY_MAX_ATTEMPTS} failed staging "
        f"{local_path} -> {dest_url}; retrying in {wait_seconds:.1f}s ({last_exception})"
      )
      time.sleep(wait_seconds)

  raise last_exception


STAGE_BACKENDS = {
  "vub": _stage_vub_gfal,
}


def gfal_stage_output(local_path, final_path):
  # Only facilities in STAGE_BACKENDS have a remote stage-out protocol; everywhere else
  # (lxplus, naf, unknown hosts) the final path is an ordinary filesystem path, so a plain
  # copy is the correct stage-out rather than an error. Callers that want to skip staging
  # altogether should test `get_facility() in STAGE_BACKENDS` first, as condor_runner does.
  facility = get_facility()
  backend = STAGE_BACKENDS.get(facility)
  if backend is None:
    info(f"No remote stage-out backend for facility '{facility}'; copying {local_path} -> {final_path}")
    _stage_local_copy(local_path, final_path)
    return
  backend(local_path, final_path)
