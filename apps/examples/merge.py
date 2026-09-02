#!/usr/bin/env python3
import argparse
import concurrent.futures
import getpass
import glob
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from Logger import info
import teaHelpers
from teaHelpers import get_facility, validate_root_file


DEFAULT_HADD_WORKERS = min(16, os.cpu_count() or 1)
SCRATCH_SPACE_FACTOR = 2.5
FINAL_REDUCTION_WORK_FACTOR = 3.0
ETA_MIN_SAMPLE_SECONDS = 5.0
ETA_MIN_SAMPLE_FRACTION = 0.02
ETA_ADJUSTMENT_FRACTION = 0.02
MAX_PROGRESS_PER_SECOND = 4.0


def positive_int(value):
  parsed_value = int(value)
  if parsed_value < 1:
    raise argparse.ArgumentTypeError("must be at least 1")
  return parsed_value


def parse_args():
  parser = argparse.ArgumentParser(description="Merge ROOT files in batches of N.")
  parser.add_argument("--files_config", required=True, help="Path to the files config.")
  parser.add_argument(
    "-n",
    "--n-files-to-merge",
    type=int,
    default=-1,
    help="Number of input files per merged output (-1 to merge all files into a single output).",
  )
  parser.add_argument(
    "--condor",
    action="store_true",
    help="Submit one merge job per batch to HTCondor.",
  )
  parser.add_argument(
    "--dry",
    action="store_true",
    help="Print the merge plan without running hadd or submitting Condor jobs.",
  )
  parser.add_argument(
    "--add-hash",
    action="store_true",
    help="Append the CMSSW commit provenance tag to merged ROOT filenames.",
  )
  parser.add_argument(
    "--cmssw-src",
    help="CMSSW src directory used by --add-hash (default: CMSSW_SRC/workflow.env).",
  )
  parser.add_argument(
    "--commit-hash",
    help="Override the commit used by --add-hash, for example when reproducing an older input.",
  )
  parser.add_argument(
    "--skip-no-keys",
    action="store_true",
    help="Inspect input ROOT files and skip files that contain no keys before forming merge batches.",
  )
  parser.add_argument(
    "--preserve-input-compression",
    "--same-compression",
    dest="preserve_input_compression",
    action="store_true",
    help="Use hadd -fk to preserve each input basket's compression and avoid recompressing mixed inputs.",
  )
  parser.add_argument(
    "--hadd-workers",
    type=positive_int,
    default=DEFAULT_HADD_WORKERS,
    help=(
      f"Number of hadd worker processes (default: {DEFAULT_HADD_WORKERS}, automatically capped at 16; "
      "use 1 to disable hadd multiprocessing)."
    ),
  )
  parser.add_argument(
    "--show-hadd-output",
    action="store_true",
    help="Show captured ROOT/hadd messages during local merges (Condor messages are already written to job logs).",
  )
  parser.add_argument(
    "--hadd-files-per-pass",
    type=positive_int,
    help=(
      "Limit the number of input files in each internal hadd pass for more frequent progress updates "
      "(default: let hadd choose; smaller values may merge more slowly)."
    ),
  )
  return parser.parse_args()


def find_workflow_env():
  candidates = []
  for start in (Path.cwd(), Path(__file__).resolve()):
    for parent in (start, *start.parents):
      candidates.append(parent / "shift_cmssw_workflow" / "config" / "workflow.env")
  return next((path for path in candidates if path.is_file()), None)


def cmssw_src_from_workflow():
  workflow_env = find_workflow_env()
  if workflow_env is None:
    return None
  clean_environment = {key: value for key, value in os.environ.items() if key != "BASH_ENV"}
  result = subprocess.run(
    [
      "bash",
      "--noprofile",
      "--norc",
      "-c",
      'source "$1" >/dev/null && printf "%s" "$CMSSW_SRC"',
      "bash",
      str(workflow_env),
    ],
    check=False,
    capture_output=True,
    text=True,
    env=clean_environment,
  )
  return result.stdout if result.returncode == 0 and result.stdout else None


def cmssw_provenance_tag(cmssw_src=None, commit_hash=None):
  if commit_hash:
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit_hash):
      raise ValueError("--commit-hash must contain 7 to 40 hexadecimal characters")
    return commit_hash.lower()

  source_dir = cmssw_src or os.environ.get("CMSSW_SRC") or cmssw_src_from_workflow()
  if not source_dir:
    raise RuntimeError("Could not determine CMSSW_SRC; source workflow.env or pass --cmssw-src/--commit-hash")

  git_command = ["git", "-C", source_dir]
  try:
    commit = subprocess.run(
      [*git_command, "rev-parse", "--short=12", "HEAD"],
      check=True,
      capture_output=True,
      text=True,
    ).stdout.strip()
    diff = subprocess.run(
      [*git_command, "diff", "HEAD", "--binary"],
      check=True,
      capture_output=True,
    ).stdout
  except subprocess.CalledProcessError as error:
    raise RuntimeError(f"Could not derive CMSSW commit from '{source_dir}'") from error

  if diff:
    return f"{commit}-dirty-{hashlib.sha256(diff).hexdigest()[:8]}"
  return commit


def load_files_config(config_path):
  spec = importlib.util.spec_from_file_location("files_config", config_path)
  files_config = importlib.util.module_from_spec(spec)
  sys.modules["files_config"] = files_config
  spec.loader.exec_module(files_config)
  return files_config


def chunk_files(file_paths, chunk_size):
  return [file_paths[index : index + chunk_size] for index in range(0, len(file_paths), chunk_size)]


def format_duration(seconds):
  total_seconds = max(0, int(seconds + 0.5))
  hours, remainder = divmod(total_seconds, 3600)
  minutes, seconds = divmod(remainder, 60)
  return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_file_size(size_bytes):
  size = float(size_bytes)
  for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
    if size < 1024 or unit == "TiB":
      return f"{size:.1f} {unit}"
    size /= 1024


def print_file_progress(current_file, total_files, suffix=None):
  percentage = (current_file * 100) // total_files if total_files else 100
  width = 50
  position = (percentage * width) // 100
  progress_bar = "\r\033[2K\033[1;92m["
  for bar_index in range(width):
    if bar_index < position:
      progress_bar += "="
    elif bar_index == position:
      progress_bar += ">"
    else:
      progress_bar += " "
  progress_bar += f"] {percentage}% (File {current_file}/{total_files})"
  if suffix:
    progress_bar += f" | {suffix}"
  info(progress_bar, end="")
  sys.stdout.flush()


def print_merge_progress(percentage, suffix=None):
  percentage = max(0, min(100, percentage))
  width = 50
  position = int(percentage * width / 100)
  progress_bar = "\r\033[2K\033[1;92m["
  for bar_index in range(width):
    if bar_index < position:
      progress_bar += "="
    elif bar_index == position:
      progress_bar += ">"
    else:
      progress_bar += " "
  progress_bar += f"] {percentage:.0f}%"
  if suffix:
    progress_bar += f" | {suffix}"
  info(progress_bar, end="")
  sys.stdout.flush()


class MergeProgress:
  def __init__(
    self,
    total_files,
    expected_output_size,
    output_expected_sizes,
    parallel_outputs,
    stage_outputs,
  ):
    self.total_files = total_files
    self.expected_output_size = expected_output_size
    self.output_expected_sizes = output_expected_sizes
    self.output_files = list(output_expected_sizes)
    self.parallel_outputs = set(parallel_outputs)
    self.stage_outputs = stage_outputs
    self.working_outputs = {}
    self.partial_dirs = {}
    self.reducing_outputs = set()
    self.staging_outputs = set()
    self.completed_outputs = set()
    self.merged_files = 0
    self.warning_count = 0
    self.error_count = 0
    self.lock = threading.Lock()
    self.start_time = None
    self.initial_output_stats = {}
    self.output_work_floors = {}
    self.estimated_total_duration = None
    self.throughput_samples = []
    self.displayed_percentage = 0.0
    self.last_display_time = None
    self.stop_event = threading.Event()
    self.refresh_thread = None
    self.refresh_interval = 1.0

  def start(self):
    self.start_time = time.monotonic()
    self.last_display_time = self.start_time
    for output_file in self.output_files:
      try:
        output_stat = os.stat(output_file)
        self.initial_output_stats[output_file] = (
          output_stat.st_mtime_ns,
          output_stat.st_size,
        )
      except OSError:
        self.initial_output_stats[output_file] = None
    info(
      f"Merging {self.total_files} input ROOT files; "
      f"rough expected output size: {format_file_size(self.expected_output_size)}"
    )
    self._print_progress(self.start_time)
    self.refresh_thread = threading.Thread(target=self._refresh_eta, daemon=True)
    self.refresh_thread.start()

  def register_working_output(self, output_file, working_output, partial_dir=None):
    with self.lock:
      self.working_outputs[output_file] = working_output
      if working_output != output_file:
        self.initial_output_stats[output_file] = None
      if partial_dir:
        self.partial_dirs[output_file] = partial_dir

  def mark_staging(self, output_file):
    with self.lock:
      self.partial_dirs.pop(output_file, None)
      self.reducing_outputs.discard(output_file)
      self.staging_outputs.add(output_file)
      self._print_progress(time.monotonic())

  def complete_output(self, output_file, n_files):
    with self.lock:
      self.partial_dirs.pop(output_file, None)
      self.reducing_outputs.discard(output_file)
      self.staging_outputs.discard(output_file)
      self.completed_outputs.add(output_file)
      self.merged_files = min(self.merged_files + n_files, self.total_files)
      self._print_progress(time.monotonic())

  def unregister_working_output(self, output_file):
    with self.lock:
      self.working_outputs.pop(output_file, None)
      self.partial_dirs.pop(output_file, None)
      self.reducing_outputs.discard(output_file)
      self.staging_outputs.discard(output_file)

  def _modified_output_size(self, output_file):
    working_output = self.working_outputs.get(output_file, output_file)
    try:
      output_stat = os.stat(working_output)
    except OSError:
      return 0
    current_stat = (output_stat.st_mtime_ns, output_stat.st_size)
    if current_stat == self.initial_output_stats[output_file]:
      return 0
    return output_stat.st_size

  def _current_output_status(self):
    current_size = 0
    completed_work = 0
    total_work = 0
    phases = set()
    for output_file in self.output_files:
      expected_size = self.output_expected_sizes[output_file]
      is_parallel = output_file in self.parallel_outputs
      output_total_work = expected_size
      if is_parallel:
        output_total_work += FINAL_REDUCTION_WORK_FACTOR * expected_size
      total_work += output_total_work

      if output_file in self.completed_outputs:
        current_size += expected_size
        completed_work += output_total_work
        phases.add("Completed output")
        continue

      if output_file in self.staging_outputs:
        current_size += self._modified_output_size(output_file)
        completed_work += output_total_work
        phases.add("Staging output")
        continue

      if output_file not in self.working_outputs:
        phases.add("Waiting for merge")
        continue

      output_size = self._modified_output_size(output_file)
      partial_dir = self.partial_dirs.get(output_file)
      if not partial_dir:
        current_size += output_size
        output_work = min(output_size, expected_size)
        phases.add("Writing local output" if self.stage_outputs else "Writing output")
      else:
        partial_size = 0
        for partial_file in glob.glob(f"{partial_dir}/partial*.root"):
          try:
            partial_size += os.path.getsize(partial_file)
          except OSError:
            # hadd may remove partials while the monitor is reading the directory.
            pass
        reduction_threshold = max(
          4 * 1024,
          self.output_expected_sizes[output_file] // 100,
        )
        if output_size >= reduction_threshold:
          self.reducing_outputs.add(output_file)

        if output_file in self.reducing_outputs:
          current_size += output_size
          output_work = expected_size + FINAL_REDUCTION_WORK_FACTOR * min(output_size, expected_size)
          phases.add("Final reduction")
        else:
          current_size += partial_size
          output_work = min(partial_size, expected_size)
          phases.add("Parallel partial merge")

      # Partial files can disappear just before hadd creates the reduction
      # target. Never let that filesystem transition move progress backwards.
      output_work = max(self.output_work_floors.get(output_file, 0), output_work)
      output_work = min(output_work, output_total_work)
      self.output_work_floors[output_file] = output_work
      completed_work += output_work

    phase = phases.pop() if len(phases) == 1 else "Merging outputs"
    return current_size, phase, completed_work, total_work

  def _update_time_estimate(self, current_time, completed_work, total_work):
    new_sample = not self.throughput_samples or completed_work > self.throughput_samples[-1][1]
    if new_sample:
      self.throughput_samples.append((current_time, completed_work))
    if not new_sample:
      return
    if len(self.throughput_samples) < 2:
      return
    first_time, first_work = self.throughput_samples[0]
    last_time, last_work = self.throughput_samples[-1]
    sample_duration = last_time - first_time
    measured_work = last_work - first_work
    minimum_sample = max(64 * 1024, ETA_MIN_SAMPLE_FRACTION * total_work)
    if sample_duration < ETA_MIN_SAMPLE_SECONDS or measured_work < minimum_sample:
      return

    work_per_second = measured_work / sample_duration
    remaining_work = max(0, total_work - completed_work)
    elapsed = current_time - self.start_time
    candidate_duration = elapsed + remaining_work / work_per_second
    if self.estimated_total_duration is None:
      self.estimated_total_duration = candidate_duration
      return

    # A cumulative rate is deliberately stable. Limit each correction as well,
    # so a newly observed phase changes the ETA over several refreshes instead
    # of producing a large one-second jump.
    blended_duration = 0.9 * self.estimated_total_duration + 0.1 * candidate_duration
    maximum_adjustment = max(
      1.0,
      ETA_ADJUSTMENT_FRACTION * self.estimated_total_duration,
    )
    adjustment = max(
      -maximum_adjustment,
      min(maximum_adjustment, blended_duration - self.estimated_total_duration),
    )
    self.estimated_total_duration += adjustment

  def _smooth_percentage(self, current_time, target_percentage):
    elapsed_since_display = max(0, current_time - self.last_display_time)
    maximum_increase = MAX_PROGRESS_PER_SECOND * elapsed_since_display
    self.displayed_percentage = max(
      self.displayed_percentage,
      min(target_percentage, self.displayed_percentage + maximum_increase),
    )
    self.last_display_time = current_time
    return self.displayed_percentage

  def _print_progress(self, current_time):
    current_size, phase, completed_work, total_work = self._current_output_status()
    self._update_time_estimate(current_time, completed_work, total_work)
    elapsed = current_time - self.start_time
    observed_percentage = 100 * completed_work / total_work if total_work else 0
    if self.estimated_total_duration is None:
      target_percentage = observed_percentage
      eta = "calculating..."
    else:
      time_percentage = 100 * elapsed / self.estimated_total_duration
      target_percentage = max(observed_percentage, time_percentage)
      eta = format_duration(max(0, self.estimated_total_duration - elapsed))

    if self.merged_files >= self.total_files:
      percentage = 100
      self.displayed_percentage = 100
      eta = "00:00:00"
    else:
      percentage = min(self._smooth_percentage(current_time, target_percentage), 99)
    print_merge_progress(
      percentage,
      f"{phase}: {format_file_size(current_size)} / ~{format_file_size(self.expected_output_size)} | ETA {eta}",
    )

  def _refresh_eta(self):
    while not self.stop_event.wait(self.refresh_interval):
      with self.lock:
        if self.merged_files >= self.total_files:
          continue
        current_time = time.monotonic()
        self._print_progress(current_time)

  def print_message(self, message):
    with self.lock:
      if not message.endswith("\n"):
        message += "\n"
      info(f"\r\033[2K{message}", end="")
      self._print_progress(time.monotonic())

  def print_diagnostic(self, message, level):
    with self.lock:
      if level == "error":
        self.error_count += 1
      else:
        self.warning_count += 1
      if not message.endswith("\n"):
        message += "\n"
      info(f"\r\033[2K{message}", end="")
      self._print_progress(time.monotonic())

  def finish(self, succeeded):
    self.stop_event.set()
    if self.refresh_thread is not None:
      self.refresh_thread.join()
    elapsed = time.monotonic() - self.start_time
    info("\033[0m")
    if self.warning_count or self.error_count:
      info(f"ROOT/hadd diagnostics: {self.warning_count} warning(s), {self.error_count} error(s)")
    if succeeded:
      info(f"Merge finished in {format_duration(elapsed)}")


def skip_files_without_keys(file_paths):
  files_with_keys = []
  skipped_files = []
  uninspected_files = []
  total_files = len(file_paths)
  start_time = time.monotonic()
  info(f"Checking {total_files} input ROOT files for keys...")
  if total_files:
    print_file_progress(0, total_files)

  try:
    for file_index, file_path in enumerate(file_paths, start=1):
      # Same predicate as the stage-out gate and the resubmit check; only the disposition
      # differs here -- a file we could not inspect is still handed to hadd, which has its
      # own recovery, while a file that is readable but empty is genuinely useless.
      status = teaHelpers.classify_root_file(file_path)
      if status == teaHelpers.ROOT_FILE_NO_KEYS:
        skipped_files.append(file_path)
      else:
        files_with_keys.append(file_path)
        if status not in (teaHelpers.ROOT_FILE_HEALTHY, teaHelpers.ROOT_FILE_RECOVERED):
          uninspected_files.append(file_path)

      print_file_progress(file_index, total_files)
  finally:
    if total_files:
      info("\033[0m")
  for file_path in uninspected_files:
    info(f"Could not inspect ROOT keys; leaving file for hadd to handle: {file_path}")
  for file_path in skipped_files:
    info(f"Skipping ROOT file with no keys: {file_path}")
  elapsed = time.monotonic() - start_time
  info(
    f"Key check finished in {elapsed:.1f} s: kept {len(files_with_keys)} files and skipped {len(skipped_files)} files"
  )
  return files_with_keys


def build_hadd_command(
  output_file,
  input_files,
  preserve_input_compression,
  hadd_files_per_pass=None,
  hadd_workers=4,
  partial_dir=None,
):
  force_option = "-fk" if preserve_input_compression else "-f"
  command = ["hadd", force_option]
  if hadd_workers > 1:
    command.extend(["-j", str(hadd_workers)])
    if partial_dir:
      command.extend(["-d", partial_dir])
  command.extend(["-k", "-v", "99"])
  if hadd_files_per_pass is not None:
    # hadd's -n limit includes the target file itself.
    command.extend(["-n", str(hadd_files_per_pass + 1)])
  return [*command, output_file, *input_files]


def run_command(command):
  subprocess.run(command, check=True)


def choose_scratch_root(required_bytes):
  candidates = []
  configured_tmp = os.environ.get("TMPDIR")
  if configured_tmp:
    candidates.append(configured_tmp)
  candidates.append(os.path.join("/tmp", getpass.getuser()))

  checked_candidates = set()
  for candidate in candidates:
    candidate = os.path.abspath(candidate)
    if candidate in checked_candidates or candidate.startswith("/eos/"):
      continue
    checked_candidates.add(candidate)
    try:
      os.makedirs(candidate, mode=0o700, exist_ok=True)
      probe_dir = tempfile.mkdtemp(prefix=".tea_merge_probe_", dir=candidate)
      os.rmdir(probe_dir)
      free_bytes = shutil.disk_usage(candidate).free
    except OSError as error:
      info(f"Scratch location {candidate} is unavailable: {error}")
      continue

    if free_bytes < required_bytes:
      info(
        f"Scratch location {candidate} has {format_file_size(free_bytes)} free; "
        f"need approximately {format_file_size(required_bytes)}"
      )
      continue
    return candidate

  return None


def contains_top_level_tree(file_path):
  import ROOT

  previous_error_level = ROOT.gErrorIgnoreLevel
  ROOT.gErrorIgnoreLevel = ROOT.kFatal
  try:
    root_file = ROOT.TFile.Open(file_path, "READ")
    if not root_file or root_file.IsZombie():
      if root_file:
        root_file.Close()
      return True
    for key in root_file.GetListOfKeys():
      root_class = ROOT.gROOT.GetClass(key.GetClassName())
      if root_class and root_class.InheritsFrom(ROOT.TTree.Class()):
        root_file.Close()
        return True
    root_file.Close()
    return False
  finally:
    ROOT.gErrorIgnoreLevel = previous_error_level


def stage_output(local_output, output_file):
  # One stage-out implementation for the whole toolkit: temp name -> transport with retry
  # -> atomic rename, with the transport chosen from the facility. Kept as a named
  # function because the merge call site reads better with the local vocabulary.
  teaHelpers.stage_output(local_output, output_file)


def hadd_diagnostic_level(output_line):
  if re.search(r"(?i)(fatal|syserror|error|failed|failure|zombie|corrupt)", output_line):
    return "error"
  if re.search(r"(?i)(warning|missing.*keys?|no keys?)", output_line):
    return "warning"
  return None


def run_hadd(
  command,
  input_files,
  merge_progress,
  hadd_files_per_pass=None,
  show_hadd_output=False,
  partial_dir=None,
):
  process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
  )
  output_lines = []

  for output_line in process.stdout:
    output_lines.append(output_line)
    diagnostic_level = hadd_diagnostic_level(output_line)
    if diagnostic_level:
      merge_progress.print_diagnostic(output_line, diagnostic_level)
    elif show_hadd_output:
      merge_progress.print_message(output_line)

  return_code = process.wait()
  if return_code != 0:
    if show_hadd_output:
      raise RuntimeError(f"hadd failed with exit code {return_code}; captured output was shown above")
    output = "".join(output_lines)
    raise RuntimeError(f"hadd failed with exit code {return_code}. Captured output:\n{output}")


def write_file(path, content):
  with open(path, "w", encoding="utf-8") as output_file:
    output_file.write(content)


def get_merge_targets(files_config):
  # An empty output_*_dir means "this stage produces no output of that kind" (the same
  # convention SubmissionManager and condor_runner use). Taking it at face value here
  # globs the CWD instead: base "" yields the pattern "./*.root" and the output directory
  # "./_merged".
  targets = []

  if getattr(files_config, "output_hists_dir", ""):
    targets.append(("histograms", files_config.output_hists_dir))

  if getattr(files_config, "output_trees_dir", ""):
    targets.append(("trees", files_config.output_trees_dir))

  return targets


def build_sample_dir(base_dir, sample):
  normalized_base_dir = os.path.normpath(base_dir)
  parent_dir = os.path.dirname(normalized_base_dir)
  leaf_dir = os.path.basename(normalized_base_dir)

  if not parent_dir or parent_dir == normalized_base_dir:
    return os.path.join(normalized_base_dir, sample)

  return os.path.join(parent_dir, sample, leaf_dir)


def collect_jobs(
  samples,
  base_dir,
  merge_kind,
  chunk_size,
  provenance_tag,
  skip_no_keys,
  input_file_pattern="*.root",
  explicit_input_files=None,
):
  jobs = []
  info(f"[{merge_kind}] base dir: {base_dir}")

  for sample in samples:
    input_dir = build_sample_dir(base_dir, sample)
    output_dir = f"{input_dir}_merged"

    info(f"[{merge_kind}] sample: {sample}")
    info(f"[{merge_kind}] deduced input dir: {input_dir}")
    info(f"[{merge_kind}] deduced output dir: {output_dir}")

    if explicit_input_files is not None:
      input_files = list(explicit_input_files)
      info(f"[{merge_kind}] using {len(input_files)} explicitly listed input files")
    else:
      input_pattern = os.path.join(input_dir, input_file_pattern)
      info(f"[{merge_kind}] deduced input pattern: {input_pattern}")
      input_files = sorted(glob.glob(input_pattern))
      info(f"[{merge_kind}] found {len(input_files)} files for sample {sample}")

    if not input_files:
      continue

    if skip_no_keys:
      input_files = skip_files_without_keys(input_files)
      if not input_files:
        info(f"[{merge_kind}] no files with ROOT keys remain for sample {sample}")
        continue

    provenance_suffix = f"_{provenance_tag}" if provenance_tag else ""
    if chunk_size == -1:
      output_file = os.path.join(output_dir, f"ntuple_0{provenance_suffix}.root")
      jobs.append((merge_kind, sample, 0, input_dir, output_dir, output_file, input_files))
    else:
      for batch_index, batch_files in enumerate(chunk_files(input_files, chunk_size)):
        output_file = os.path.join(output_dir, f"ntuple_{batch_index}{provenance_suffix}.root")
        jobs.append((merge_kind, sample, batch_index, input_dir, output_dir, output_file, batch_files))

  return jobs


def print_job_summary(jobs, use_condor):
  mode = "condor" if use_condor else "local"
  info(f"Dry run: planned {len(jobs)} merge jobs in {mode} mode")

  for merge_kind, sample, batch_index, input_dir, output_dir, output_file, input_files in jobs:
    info(f"Type: {merge_kind}")
    info(f"Sample: {sample}")
    info(f"  input dir: {input_dir}")
    info(f"  output dir: {output_dir}")
    info(f"  batch {batch_index}:")
    info(f"    output: {output_file}")
    for input_file in input_files:
      info(f"    input: {input_file}")


def create_condor_job(
  condor_dir,
  merge_kind,
  sample,
  batch_index,
  output_file,
  input_files,
  preserve_input_compression,
  hadd_files_per_pass,
  hadd_workers,
):
  safe_sample = sample.replace("/", "_")
  script_path = os.path.join(condor_dir, f"{merge_kind}_{safe_sample}_{batch_index}.sh")
  hadd_command = build_hadd_command(
    output_file,
    input_files,
    preserve_input_compression,
    hadd_files_per_pass,
    hadd_workers,
  )

  script_content = "\n".join(
    [
      "#!/bin/bash",
      "set -e",
      "touch condor_dummy.out",
      f"mkdir -p {shlex.quote(os.path.dirname(output_file))}",
      shlex.join(hadd_command),
      "",
    ]
  )
  write_file(script_path, script_content)
  os.chmod(script_path, 0o755)
  return script_path


def submit_condor_jobs(
  condor_dir,
  jobs,
  preserve_input_compression,
  hadd_files_per_pass,
  hadd_workers,
):
  os.makedirs(condor_dir, exist_ok=True)
  facility = get_facility()

  executable_paths = [
    create_condor_job(
      condor_dir,
      merge_kind,
      sample,
      batch_index,
      output_file,
      input_files,
      preserve_input_compression,
      hadd_files_per_pass,
      hadd_workers,
    )
    for merge_kind, sample, batch_index, _, _, output_file, input_files in jobs
  ]

  submit_lines = [
    "universe = vanilla",
    "getenv = True",
    "executable = $(script)",
    f"log = {condor_dir}/$(ClusterId).$(ProcId).log",
    f"output = {condor_dir}/$(ClusterId).$(ProcId).out",
    f"error = {condor_dir}/$(ClusterId).$(ProcId).err",
    f"request_cpus = {hadd_workers}",
  ]

  if facility == "lxplus":
    submit_lines.extend(
      [
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        "transfer_output_files = condor_dummy.out",
      ]
    )
  else:
    submit_lines.append("should_transfer_files = NO")

  submit_lines.extend(
    [
      "queue script from (",
      *executable_paths,
      ")",
      "",
    ]
  )

  submit_path = os.path.join(condor_dir, "merge.sub")
  submit_content = "\n".join(submit_lines)
  write_file(submit_path, submit_content)

  command = ["condor_submit", submit_path]
  if facility == "lxplus":
    command = ["condor_submit", "-spool", submit_path]

  run_command(command)


def run_jobs_locally(
  merge_jobs,
  preserve_input_compression,
  merge_progress,
  hadd_files_per_pass,
  hadd_workers,
  show_hadd_output,
  scratch_root,
):
  for _, _, _, _, output_dir, output_file, input_files in merge_jobs:
    os.makedirs(output_dir, exist_ok=True)
    job_workers = min(hadd_workers, len(input_files))
    work_dir = None
    partial_dir = None
    working_output = output_file
    if scratch_root:
      work_dir = tempfile.mkdtemp(prefix="tea_merge_", dir=scratch_root)
      working_output = os.path.join(work_dir, os.path.basename(output_file))
      if job_workers > 1:
        partial_dir = os.path.join(work_dir, "partials")
        os.makedirs(partial_dir)
    elif job_workers > 1:
      partial_dir = tempfile.mkdtemp(prefix=".hadd_partials_", dir=output_dir)

    merge_progress.register_working_output(output_file, working_output, partial_dir)
    job_succeeded = False
    try:
      command = build_hadd_command(
        working_output,
        input_files,
        preserve_input_compression,
        hadd_files_per_pass,
        job_workers,
        partial_dir,
      )
      run_hadd(
        command,
        input_files,
        merge_progress,
        hadd_files_per_pass,
        show_hadd_output,
        partial_dir,
      )
      validate_root_file(working_output)
      if scratch_root:
        merge_progress.mark_staging(output_file)
        stage_output(working_output, output_file)
      merge_progress.complete_output(output_file, len(input_files))
      job_succeeded = True
    finally:
      merge_progress.unregister_working_output(output_file)
      if work_dir and job_succeeded:
        shutil.rmtree(work_dir, ignore_errors=True)
      elif work_dir:
        info(f"Preserving failed merge workspace for inspection: {work_dir}")
      elif partial_dir:
        shutil.rmtree(partial_dir, ignore_errors=True)


def main():
  args = parse_args()
  if not args.add_hash and (args.cmssw_src or args.commit_hash):
    raise ValueError("--cmssw-src and --commit-hash require --add-hash")
  provenance_tag = None
  if args.add_hash:
    provenance_tag = cmssw_provenance_tag(args.cmssw_src, args.commit_hash)
    info(f"CMSSW provenance tag: {provenance_tag}")

  files_config = load_files_config(args.files_config)
  samples = files_config.samples if hasattr(files_config, "samples") else [""]
  input_file_pattern = getattr(files_config, "input_file_pattern", "*.root")
  if os.path.basename(input_file_pattern) != input_file_pattern:
    raise ValueError("input_file_pattern must be a basename glob, not a path")

  explicit_input_files = getattr(files_config, "input_files", None)
  if explicit_input_files is not None:
    if hasattr(files_config, "samples") and list(files_config.samples) != [""]:
      raise ValueError("input_files cannot be combined with an explicit samples list")
    # Sorted, so an explicit list keeps the deterministic chunk -> ntuple_N.root mapping
    # that the glob branch gets from sorted(glob.glob(...)).
    explicit_input_files = sorted(explicit_input_files)
    if not explicit_input_files:
      raise ValueError("input_files must be a non-empty list of file paths")
    missing_files = [path for path in explicit_input_files if not os.path.isfile(path)]
    if missing_files:
      raise ValueError(f"input_files lists {len(missing_files)} file(s) that do not exist: {missing_files[:5]}")
    # realpath, because results-unmerged/ is itself a symlink: two textually distinct tag
    # vintages can name one file, and hadd would then double-count its events and exit 0.
    resolved_files = [os.path.realpath(path) for path in explicit_input_files]
    duplicate_files = sorted({path for path in resolved_files if resolved_files.count(path) > 1})
    if duplicate_files:
      raise ValueError(
        f"input_files lists {len(duplicate_files)} file(s) more than once (after resolving "
        f"symlinks), which would double-count events: {duplicate_files[:5]}"
      )

  merge_targets = get_merge_targets(files_config)
  if not merge_targets:
    raise ValueError("files_config must define output_hists_dir and/or output_trees_dir")
  if explicit_input_files is not None and len(merge_targets) != 1:
    raise ValueError("input_files can only be combined with exactly one of output_hists_dir/output_trees_dir")

  jobs_by_kind = []
  for merge_kind, base_dir in merge_targets:
    jobs = collect_jobs(
      samples,
      base_dir,
      merge_kind,
      args.n_files_to_merge,
      provenance_tag,
      args.skip_no_keys,
      input_file_pattern,
      explicit_input_files,
    )
    if jobs:
      jobs_by_kind.append((merge_kind, base_dir, jobs))

  jobs = [job for _, _, merge_jobs in jobs_by_kind for job in merge_jobs]

  if not jobs:
    info("No input files found to merge.")
    return

  if args.dry:
    print_job_summary(jobs, args.condor)
    return

  if args.condor:
    condor_base_dir = os.path.join("tmp", "condor_merge")
    os.makedirs(condor_base_dir, exist_ok=True)

    for merge_kind, _, merge_jobs in jobs_by_kind:
      submit_condor_jobs(
        os.path.join(condor_base_dir, merge_kind),
        merge_jobs,
        args.preserve_input_compression,
        args.hadd_files_per_pass,
        args.hadd_workers,
      )
    return

  input_files = [input_file for job in jobs for input_file in job[-1]]
  job_input_sizes = {job[5]: sum(os.path.getsize(input_file) for input_file in job[-1]) for job in jobs}
  output_expected_sizes = {}
  for _, _, merge_jobs in jobs_by_kind:
    contains_trees = contains_top_level_tree(merge_jobs[0][-1][0])
    for job in merge_jobs:
      output_expected_sizes[job[5]] = (
        job_input_sizes[job[5]] if contains_trees else max(os.path.getsize(input_file) for input_file in job[-1])
      )
  expected_output_size = sum(output_expected_sizes.values())
  peak_input_size = sum(max(job_input_sizes[job[5]] for job in merge_jobs) for _, _, merge_jobs in jobs_by_kind)
  required_scratch_bytes = int(SCRATCH_SPACE_FACTOR * peak_input_size)
  scratch_root = choose_scratch_root(required_scratch_bytes)
  if scratch_root:
    info(
      f"Using local merge scratch: {scratch_root} ({format_file_size(required_scratch_bytes)} estimated requirement)"
    )
  else:
    info("Local scratch is unavailable or too small; merging in the output directory")
  info(f"Using up to {args.hadd_workers} hadd worker processes per merge")

  merge_progress = MergeProgress(
    len(input_files),
    expected_output_size,
    output_expected_sizes,
    [job[5] for job in jobs if min(args.hadd_workers, len(job[-1])) > 1],
    scratch_root is not None,
  )
  merge_progress.start()
  merge_succeeded = False
  try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs_by_kind)) as executor:
      futures = [
        executor.submit(
          run_jobs_locally,
          merge_jobs,
          args.preserve_input_compression,
          merge_progress,
          args.hadd_files_per_pass,
          args.hadd_workers,
          args.show_hadd_output,
          scratch_root,
        )
        for _, _, merge_jobs in jobs_by_kind
      ]
      for future in futures:
        future.result()
    merge_succeeded = True
  finally:
    merge_progress.finish(merge_succeeded)


if __name__ == "__main__":
  main()
