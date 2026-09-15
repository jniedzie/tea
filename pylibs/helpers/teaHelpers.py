import re
import functools
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

# Where a bare LFN ("/store/...") is published, and how it is spelled on the door. The
# site's namespace prefix is *not* part of the LFN by design: configs hold bare LFNs at
# every site (so path arithmetic keeps working) and the storage prefix is applied only
# here, at the moment of I/O.
STAGE_URL_BASE = os.environ.get("TEA_STAGE_URL_BASE", GFAL_DOOR)
STAGE_LFN_PREFIX = os.environ.get("TEA_STAGE_LFN_PREFIX", "/pnfs/iihe/cms")

# Redirector used to *read* an LFN (classify_root_file). Callers that know their site's
# door pass it explicitly; this is only the fallback.
XROOTD_REDIRECTOR = os.environ.get("TEA_XROOTD_REDIRECTOR", "cms-xrd-global.cern.ch")

LFN_ROOT = "/store/"

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


def is_lfn(path):
  """True for a bare CMS logical file name, i.e. a path under /store/.

  Such a path exists in no local namespace: it can be neither os.makedirs'd nor
  os.path.exists'd, and every access to it has to go through a door.
  """
  return str(path).startswith(LFN_ROOT)


def read_url(file_path, redirector=None):
  """URL to read file_path with. Non-LFN paths are returned unchanged.

  The double slash after the host is deliberate: in xrootd it marks an absolute
  server-side path, and several servers mis-resolve the single-slash spelling.
  """
  if not is_lfn(file_path):
    return file_path
  redirector = redirector or XROOTD_REDIRECTOR
  if not redirector.startswith("root://"):
    redirector = f"root://{redirector}"
  return f"{redirector}/{file_path}"


def classify_root_file(file_path, redirector=None):
  """Classify a ROOT file as healthy, missing, unreadable (zombie), recovered or key-less.

  One predicate for every caller that asks "did this file come out intact?". A file with
  zero keys and a zero exit code is genuinely anomalous -- HistogramsHandler always writes
  its declared histograms and EventWriter always writes its tree -- so zero keys counts as
  unhealthy just like a zombie does. Callers differ only in what they *do* with each
  outcome (raise, resubmit, or hand the file to hadd anyway).
  """
  import ROOT

  # An LFN has no local existence to test, so the open *is* the test: a file that is not
  # there comes back as unreadable rather than missing. Callers only ever branch on
  # "healthy or not", so the two are interchangeable for them -- but keeping the
  # os.path.exists short-circuit here would report every LFN as missing, which is what
  # used to make __keep_only_failed_inputs resubmit an entire successful submission.
  if is_lfn(file_path):
    file_path = read_url(file_path, redirector)
  elif not os.path.exists(file_path):
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


def is_root_file_healthy(file_path, redirector=None):
  return classify_root_file(file_path, redirector) == ROOT_FILE_HEALTHY


def validate_root_file(file_path, redirector=None):
  status = classify_root_file(file_path, redirector)
  # A recovered file is tolerated here (it still holds readable keys); the stage-out gate
  # only refuses files that are unreadable or empty.
  if status in (ROOT_FILE_MISSING, ROOT_FILE_UNREADABLE, ROOT_FILE_NO_KEYS):
    raise RuntimeError(f"ROOT file is invalid or contains no keys ({status}): {file_path}")


def _dcache_gfal_url(final_path, url_base=None):
  # final_path is typically a symlink into pnfs (e.g. results/results-unmerged ->
  # /pnfs/iihe/...); realpath resolves both the symlink and dCache's local mount
  # prefix, neither of which the davs door accepts directly.
  real_path = os.path.normpath(os.path.realpath(final_path))
  if real_path.startswith(DCACHE_LOCAL_PREFIX + "/pnfs/"):
    real_path = real_path[len(DCACHE_LOCAL_PREFIX) :]
  if not real_path.startswith("/pnfs/"):
    return None
  return (url_base or STAGE_URL_BASE) + real_path


def stage_dest_url(final_path, url_base=None):
  """Door URL to publish final_path at, or None when it is an ordinary local path.

  Two cases, and the order between them matters. An LFN is checked *first*, because
  os.path.realpath("/store/...") on a machine with no such path returns the string
  unchanged -- it would then fail the /pnfs/ test below, fall through to None, and the
  caller would write a literal "/store/..." file on the worker's root filesystem. That
  silent local copy is the exact failure this function exists to remove.
  """
  if not final_path:
    return None
  if is_lfn(final_path):
    return (url_base or STAGE_URL_BASE) + STAGE_LFN_PREFIX + str(final_path)
  return _dcache_gfal_url(final_path, url_base)


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


_gfal_interpreter = False  # False = not looked for yet; None = none found


def _find_gfal_interpreter():
  """An interpreter that can actually import the gfal2 bindings.

  /usr/bin/gfal-copy is a shell wrapper that probes for one itself, but its probe runs
  the first python3 on PATH -- which, with a conda/micromamba analysis environment
  active, has no gfal2 -- and then falls back to /usr/bin/python, absent on EL9. The
  wrapper then dies with "No such file or directory" *and exits 0*, so the copy silently
  does nothing. Setting GFAL_PYTHONBIN short-circuits that probe.
  """
  global _gfal_interpreter
  if _gfal_interpreter is not False:
    return _gfal_interpreter

  candidates = ["/usr/bin/python3", "/usr/bin/python", shutil.which("python3"), shutil.which("python")]
  _gfal_interpreter = None
  for candidate in candidates:
    if not candidate or not os.path.exists(candidate):
      continue
    try:
      probe = subprocess.run(
        [candidate, "-c", "import gfal2, gfal2_util"],
        check=False,
        capture_output=True,
        timeout=60,
      )
    except (OSError, subprocess.SubprocessError):
      continue
    if probe.returncode == 0:
      _gfal_interpreter = candidate
      break

  if _gfal_interpreter is None:
    warn("No interpreter on this node can import gfal2; gfal-copy may silently do nothing")
  return _gfal_interpreter


def _gfal_environment():
  environment = os.environ.copy()
  if environment.get("GFAL_PYTHONBIN"):
    return environment
  interpreter = _find_gfal_interpreter()
  if interpreter:
    environment["GFAL_PYTHONBIN"] = interpreter
  return environment


def _run_transport_command(command, description, environment=None):
  try:
    result = subprocess.run(
      command,
      check=False,
      capture_output=True,
      text=True,
      timeout=STAGE_SUBPROCESS_TIMEOUT_SECONDS,
      env=environment,
    )
  except subprocess.TimeoutExpired as timeout:
    raise RuntimeError(f"{description} timed out after {STAGE_SUBPROCESS_TIMEOUT_SECONDS} s") from timeout

  if result.returncode != 0:
    raise RuntimeError(
      f"{description} failed (exit {result.returncode}): "
      f"stdout={result.stdout.strip()!r} stderr={result.stderr.strip()!r}"
    )
  return result


def _confirm_gfal_destination(dest_url, environment):
  """Confirm the copy actually landed. Never trust gfal-copy's exit code alone.

  A broken interpreter probe (see _find_gfal_interpreter) makes the wrapper exit 0
  without transferring anything, so a job would report every stage-out as successful and
  lose the file. gfal-stat is checked for a non-empty stdout as well as a zero exit,
  since the same broken wrapper would also "succeed" silently.
  """
  if shutil.which("gfal-stat") is None:
    warn(f"gfal-stat is not on PATH; cannot confirm {dest_url} was written")
    return
  result = _run_transport_command(["gfal-stat", dest_url], f"gfal-stat {dest_url}", environment)
  if not result.stdout.strip():
    raise RuntimeError(
      f"gfal-stat {dest_url} returned no output; the copy reported success but the "
      f"destination cannot be confirmed (is gfal's python interpreter usable?)"
    )


def _transport_filesystem(local_path, stage_path, url_base=None):
  os.makedirs(os.path.dirname(os.path.abspath(stage_path)), exist_ok=True)
  shutil.copyfile(local_path, stage_path)


def _transport_gfal(local_path, stage_path, url_base=None):
  dest_url = stage_dest_url(stage_path, url_base)
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
  # -p: creates the remote parent tree, which is why a remote destination needs no
  # equivalent of stage_output's makedirs.
  environment = _gfal_environment()
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
    environment,
  )
  _confirm_gfal_destination(dest_url, environment)


def _transport_xrootd(local_path, stage_path, url_base=None):
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
  _transport_gfal: ("gfal-copy", stage_dest_url, True),
  _transport_xrootd: ("xrdcp", eos_xrootd_url, False),
}


def get_transport(facility=None):
  if facility is None:
    facility = get_facility()
  return TRANSPORTS.get(facility, _transport_filesystem)


def select_transport(final_path, facility=None, url_base=None):
  """Pick the transport from the *destination*, falling back to the facility table.

  A destination that resolves to a door URL needs gfal wherever the job happens to run:
  keying this off the hostname is what sent an LFN output on lxplus through the EOS
  transport, which produced no URL and silently degraded to writing a literal
  "/store/..." file on the worker. The facility table still gets to choose when there is
  no door URL -- that is where the local-EOS xrdcp optimisation lives.
  """
  if stage_dest_url(final_path, url_base) is not None:
    return _transport_gfal
  return get_transport(facility)


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


def stage_output(local_path, final_path, facility=None, url_base=None):
  """Publish local_path at final_path atomically: copy to a temp name, then rename.

  Writing straight onto the final name is what makes a failed or interrupted transfer
  leave a truncated file where the next stage expects a complete one. Both URL builders
  derive their URL from a POSIX path, so the staged file is always visible to os.replace
  on the node regardless of which transport moved the bytes.

  A destination that resolves to a door URL takes a different route: gfal-copy writes
  straight to it. The dot-file-then-rename dance needs a POSIX directory it can create,
  build a sibling name in, and os.replace within -- an LFN destination fails at the first
  of those. Nothing is lost by skipping it: gfal-copy to dCache is not a streaming
  in-place write, so a failed transfer leaves no truncated file at the final name.
  """
  dest_url = stage_dest_url(final_path, url_base)
  if dest_url is not None:
    # partial rather than a third positional argument, so a transport stays a plain
    # (local_path, stage_path) callable everywhere _stage_with_retries is concerned.
    _stage_with_retries(functools.partial(_transport_gfal, url_base=url_base), local_path, final_path)
    return

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


def stage_preflight(final_paths, facility=None, url_base=None):
  """Check, before the app runs, that stage-out can work at all.

  Returns (ok, reason). A job that cannot stage out should learn it in the first seconds,
  not after hours of computation whose output then has to be discarded.
  """
  paths = [path for path in final_paths if path]

  # Per destination, not per facility: one job's outputs can legitimately need different
  # transports, and it is the destination that decides (see select_transport).
  paths_by_transport = {}
  for path in paths:
    paths_by_transport.setdefault(select_transport(path, facility, url_base), []).append(path)

  ready = []
  for transport, transport_paths in paths_by_transport.items():
    requirements = _TRANSPORT_REQUIREMENTS.get(transport)
    if requirements is None:
      continue  # filesystem stage-out needs no external transport

    binary, url_builder, needs_proxy = requirements
    remote_paths = [path for path in transport_paths if url_builder(path) is not None]
    if not remote_paths:
      continue

    if shutil.which(binary) is None:
      return False, f"{binary} is not on PATH but {len(remote_paths)} output(s) need it"

    proxy_path = os.environ.get("X509_USER_PROXY", "")
    if proxy_path:
      if not os.path.isfile(proxy_path) or not os.access(proxy_path, os.R_OK):
        return False, f"X509_USER_PROXY={proxy_path} is not a readable file"
    elif needs_proxy:
      return False, f"X509_USER_PROXY is not set but {binary} stage-out to {remote_paths[0]} needs a proxy"

    ready.append(f"{binary} stage-out ready for {len(remote_paths)} output(s)")

  if not ready:
    return True, "no output path resolves to a transport URL; stage-out falls back to a filesystem copy"
  return True, "; ".join(ready)
