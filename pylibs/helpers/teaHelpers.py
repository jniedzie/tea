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
import uuid
from Logger import error, info, warn


ROOT_VALIDATION_LOCK = threading.Lock()

# Site constants are overridable from the environment so a door migration, or a second
# dCache site, does not require patching tea.
GFAL_DOOR = os.environ.get("TEA_GFAL_DOOR", "davs://maite.iihe.ac.be:2880")
DCACHE_LOCAL_PREFIX = os.environ.get("TEA_DCACHE_LOCAL_PREFIX", "/dcache_mnt/dcache")

GFAL_COPY_TIMEOUT_SECONDS = 600
GFAL_COPY_MAX_ATTEMPTS = 5
GFAL_COPY_RETRY_BASE_WAIT_SECONDS = 20
GFAL_COPY_RETRY_EXPO_HALF_LIFE_SECONDS = 60
# The transport gets its own hard timeout on top of the protocol-level one, so a hung
# client (rather than a slow transfer) cannot pin the job until MaxWallTime.
STAGE_SUBPROCESS_TIMEOUT_SECONDS = GFAL_COPY_TIMEOUT_SECONDS + 60
# Wall-clock budget shared by every output of one job: 5 attempts x (600 s timeout +
# ~107 s mean backoff) is ~1 h per output, so trees + hists could otherwise compound into
# ~2 h of retries and push the job past its wall-time limit.
STAGE_OUT_BUDGET_SECONDS = 1800

ROOT_FILE_HEALTHY = "healthy"
ROOT_FILE_MISSING = "missing"
ROOT_FILE_UNREADABLE = "unreadable"
ROOT_FILE_NO_KEYS = "no_keys"
ROOT_FILE_RECOVERED = "recovered"

_stage_deadline = None


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
  # Only meaningful on a submit node: worker nodes often report a short hostname that
  # matches none of these patterns. Jobs receive the facility as an argument instead
  # (SubmissionManager bakes it into the run script), so they never call this.
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


def classify_root_file(file_path):
  """Classify a ROOT file as healthy, missing, unreadable (zombie), recovered or key-less.

  One predicate for every caller that asks "did this file come out intact?". A file with
  zero keys and a zero exit code is genuinely anomalous -- HistogramsHandler always writes
  its declared histograms and EventWriter always writes its tree -- so zero keys counts as
  unhealthy just like a zombie does. Callers differ only in what they *do* with each
  outcome (raise, resubmit, or hand the file to hadd anyway).
  """
  import ROOT

  if not os.path.exists(file_path):
    return ROOT_FILE_MISSING

  with ROOT_VALIDATION_LOCK:
    previous_error_level = ROOT.gErrorIgnoreLevel
    ROOT.gErrorIgnoreLevel = ROOT.kFatal
    root_file = None
    try:
      try:
        root_file = ROOT.TFile.Open(file_path, "READ")
      except OSError:
        root_file = None
      if not root_file or root_file.IsZombie():
        return ROOT_FILE_UNREADABLE
      if root_file.GetNkeys() == 0:
        return ROOT_FILE_NO_KEYS
      if root_file.TestBit(ROOT.TFile.kRecovered):
        return ROOT_FILE_RECOVERED
      return ROOT_FILE_HEALTHY
    finally:
      if root_file:
        root_file.Close()
      ROOT.gErrorIgnoreLevel = previous_error_level


def is_root_file_healthy(file_path):
  return classify_root_file(file_path) == ROOT_FILE_HEALTHY


def validate_root_file(file_path):
  status = classify_root_file(file_path)
  # A recovered file is tolerated here (it still holds readable keys); the stage-out gate
  # only refuses files that are unreadable or empty.
  if status in (ROOT_FILE_MISSING, ROOT_FILE_UNREADABLE, ROOT_FILE_NO_KEYS):
    raise RuntimeError(f"ROOT file is invalid or contains no keys ({status}): {file_path}")


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


def eos_xrootd_url(file_path):
  normalized_path = os.path.normpath(file_path)
  home_match = re.fullmatch(r"/eos/home-([^/]+)/([^/]+)(/.*)?", normalized_path)
  if home_match:
    instance, username, suffix = home_match.groups()
    return f"root://eoshome-{instance}.cern.ch//eos/user/{username[0]}/{username}{suffix or ''}"

  user_match = re.fullmatch(r"/eos/user/([^/]+)/([^/]+)(/.*)?", normalized_path)
  if user_match:
    initial, username, suffix = user_match.groups()
    return f"root://eoshome-{initial}.cern.ch//eos/user/{initial}/{username}{suffix or ''}"
  return None


def begin_stage_budget(seconds=STAGE_OUT_BUDGET_SECONDS):
  """Start (or reset) the wall-clock budget shared by every stage_output call of one job.

  Without a budget each output retries independently; a job writing both trees and
  histograms can then spend twice the per-output worst case. Long-lived processes that
  stage many unrelated outputs (merge.py) simply never call this.
  """
  global _stage_deadline
  _stage_deadline = None if seconds is None else time.monotonic() + seconds
  return _stage_deadline


def clear_stage_budget():
  global _stage_deadline
  _stage_deadline = None


def _stage_budget_remaining():
  if _stage_deadline is None:
    return None
  return _stage_deadline - time.monotonic()


def _run_transport_command(command, description):
  try:
    result = subprocess.run(
      command,
      check=False,
      capture_output=True,
      text=True,
      timeout=STAGE_SUBPROCESS_TIMEOUT_SECONDS,
    )
  except subprocess.TimeoutExpired as timeout:
    raise RuntimeError(f"{description} timed out after {STAGE_SUBPROCESS_TIMEOUT_SECONDS} s") from timeout

  if result.returncode != 0:
    raise RuntimeError(
      f"{description} failed (exit {result.returncode}): "
      f"stdout={result.stdout.strip()!r} stderr={result.stderr.strip()!r}"
    )


def _transport_filesystem(local_path, stage_path):
  os.makedirs(os.path.dirname(os.path.abspath(stage_path)), exist_ok=True)
  shutil.copyfile(local_path, stage_path)


def _transport_gfal(local_path, stage_path):
  dest_url = _dcache_gfal_url(stage_path)
  if dest_url is None:
    info(f"{stage_path} does not resolve to a pnfs path; copying directly instead of using gfal-copy")
    _transport_filesystem(local_path, stage_path)
    return
  if shutil.which("gfal-copy") is None:
    # A filesystem copy into the staging name is still atomic on publish, so a host
    # without the client degrades rather than failing. Jobs never reach this: their
    # pre-flight has already turned staging off (see stage_preflight).
    info("gfal-copy is not on PATH; copying directly instead")
    _transport_filesystem(local_path, stage_path)
    return

  # -f: dCache is write-once, so a retry's overwrite of a partial stage file needs -f to
  # replace it rather than failing with "File exists".
  _run_transport_command(
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
    f"gfal-copy {local_path} -> {dest_url}",
  )


def _transport_xrootd(local_path, stage_path):
  dest_url = eos_xrootd_url(stage_path)
  if dest_url is None:
    info(f"{stage_path} does not resolve to an EOS path; copying directly instead of using xrdcp")
    _transport_filesystem(local_path, stage_path)
    return
  if shutil.which("xrdcp") is None:
    info("xrdcp is not on PATH; copying directly instead")
    _transport_filesystem(local_path, stage_path)
    return

  _run_transport_command(
    ["xrdcp", "-f", "--cksum", "adler32", os.path.abspath(local_path), dest_url],
    f"xrdcp {local_path} -> {dest_url}",
  )


# Scratch is facility-independent (see condor_runner); only the copy protocol is not.
# naf shares dCache technology with vub, and lxplus/EOS is the textbook case of the
# mid-write corruption class this staging exists to avoid.
TRANSPORTS = {
  "vub": _transport_gfal,
  "naf": _transport_gfal,
  "lxplus": _transport_xrootd,
  "default": _transport_filesystem,
}

# transport -> (binary needed on PATH, URL builder, whether an X509 proxy is required)
_TRANSPORT_REQUIREMENTS = {
  _transport_gfal: ("gfal-copy", _dcache_gfal_url, True),
  _transport_xrootd: ("xrdcp", eos_xrootd_url, False),
}


def get_transport(facility=None):
  if facility is None:
    facility = get_facility()
  return TRANSPORTS.get(facility, _transport_filesystem)


def _stage_with_retries(transport, local_path, stage_path):
  last_exception = None

  for attempt in range(1, GFAL_COPY_MAX_ATTEMPTS + 1):
    try:
      transport(local_path, stage_path)
      return
    except Exception as exception:
      last_exception = exception

    if attempt == GFAL_COPY_MAX_ATTEMPTS:
      break

    # A constant GFAL_COPY_RETRY_BASE_WAIT_SECONDS (20 s) plus a random exponential jitter
    # with a 1-minute half-life (median wait ~80 s, mean ~107 s), so concurrent retries
    # from ~1500 jobs don't all hammer the door at the same instant (a plain fixed backoff
    # would).
    wait_seconds = GFAL_COPY_RETRY_BASE_WAIT_SECONDS + random.expovariate(
      math.log(2) / GFAL_COPY_RETRY_EXPO_HALF_LIFE_SECONDS
    )
    remaining_seconds = _stage_budget_remaining()
    if remaining_seconds is not None and remaining_seconds <= wait_seconds:
      raise RuntimeError(
        f"stage-out budget of {STAGE_OUT_BUDGET_SECONDS} s exhausted after attempt "
        f"{attempt}/{GFAL_COPY_MAX_ATTEMPTS} staging {local_path}: {last_exception}"
      ) from last_exception

    warn(
      f"stage-out attempt {attempt}/{GFAL_COPY_MAX_ATTEMPTS} failed staging "
      f"{local_path} -> {stage_path}; retrying in {wait_seconds:.1f}s ({last_exception})"
    )
    time.sleep(wait_seconds)

  raise last_exception


def stage_output(local_path, final_path, facility=None):
  """Publish local_path at final_path atomically: copy to a temp name, then rename.

  Writing straight onto the final name is what makes a failed or interrupted transfer
  leave a truncated file where the next stage expects a complete one. Both URL builders
  derive their URL from a POSIX path, so the staged file is always visible to os.replace
  on the node regardless of which transport moved the bytes.
  """
  transport = get_transport(facility)

  output_dir = os.path.dirname(os.path.abspath(final_path))
  os.makedirs(output_dir, exist_ok=True)
  stage_path = os.path.join(output_dir, f".{os.path.basename(final_path)}.stage-{uuid.uuid4().hex}")

  try:
    _stage_with_retries(transport, local_path, stage_path)
    os.replace(stage_path, final_path)
  except Exception:
    try:
      os.remove(stage_path)
    except OSError:
      pass
    raise


def stage_preflight(final_paths, facility=None):
  """Check, before the app runs, that stage-out can work at all.

  Returns (ok, reason). A job that cannot stage out should learn it in the first seconds,
  not after hours of computation whose output then has to be discarded.
  """
  transport = get_transport(facility)
  requirements = _TRANSPORT_REQUIREMENTS.get(transport)
  if requirements is None:
    return True, "filesystem stage-out needs no external transport"

  binary, url_builder, needs_proxy = requirements
  remote_paths = [path for path in final_paths if path and url_builder(path) is not None]
  if not remote_paths:
    return True, f"no output path resolves to a {binary} URL; stage-out falls back to a filesystem copy"

  if shutil.which(binary) is None:
    return False, f"{binary} is not on PATH but {len(remote_paths)} output(s) need it"

  proxy_path = os.environ.get("X509_USER_PROXY", "")
  if proxy_path:
    if not os.path.isfile(proxy_path) or not os.access(proxy_path, os.R_OK):
      return False, f"X509_USER_PROXY={proxy_path} is not a readable file"
  elif needs_proxy:
    return False, f"X509_USER_PROXY is not set but {binary} stage-out to {remote_paths[0]} needs a proxy"

  return True, f"{binary} stage-out ready for {len(remote_paths)} output(s)"
