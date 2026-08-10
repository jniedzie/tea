#!/usr/bin/env python3
import argparse
import concurrent.futures
import glob
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import threading
import time

from Logger import info
from teaHelpers import get_facility


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
    default=4,
    help="Number of hadd worker processes (default: 4; use 1 to disable hadd multiprocessing).",
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
      "bash", "--noprofile", "--norc", "-c",
      'source "$1" >/dev/null && printf "%s" "$CMSSW_SRC"', "bash", str(workflow_env),
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
  return [file_paths[index:index + chunk_size] for index in range(0, len(file_paths), chunk_size)]


def format_duration(seconds):
  total_seconds = max(0, int(seconds + 0.5))
  hours, remainder = divmod(total_seconds, 3600)
  minutes, seconds = divmod(remainder, 60)
  return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def print_file_progress(current_file, total_files, suffix=None):
  percentage = (current_file * 100) // total_files if total_files else 100
  width = 50
  position = (percentage * width) // 100
  progress_bar = "\r\033[1;92m["
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


class MergeProgress:
  def __init__(self, total_files):
    self.total_files = total_files
    self.merged_files = 0
    self.lock = threading.Lock()
    self.start_time = None
    self.eta_deadline = None
    self.eta_expired = False
    self.stop_event = threading.Event()
    self.refresh_thread = None
    self.refresh_interval = 1.0

  def start(self):
    self.start_time = time.monotonic()
    info(f"Merging {self.total_files} input ROOT files...")
    print_file_progress(0, self.total_files, "ETA --:--:--")
    self.refresh_thread = threading.Thread(target=self._refresh_eta, daemon=True)
    self.refresh_thread.start()

  def _print_progress(self, current_time):
    eta = "--:--:--"
    if self.eta_deadline is not None:
      eta = format_duration(max(0, self.eta_deadline - current_time))
    print_file_progress(
      self.merged_files,
      self.total_files,
      f"ETA {eta}",
    )

  def _refresh_eta(self):
    while not self.stop_event.wait(self.refresh_interval):
      with self.lock:
        if self.merged_files >= self.total_files or self.eta_deadline is None or self.eta_expired:
          continue
        current_time = time.monotonic()
        if self.eta_deadline - current_time < 0.5:
          self.eta_expired = True
          self._print_progress(self.eta_deadline)
        else:
          self._print_progress(current_time)

  def print_message(self, message):
    with self.lock:
      if not message.endswith("\n"):
        message += "\n"
      info(f"\r\033[2K{message}", end="")
      self._print_progress(time.monotonic())

  def advance(self, n_files=1):
    if n_files <= 0:
      return
    with self.lock:
      self.merged_files = min(self.merged_files + n_files, self.total_files)
      current_time = time.monotonic()
      elapsed = current_time - self.start_time
      remaining_files = self.total_files - self.merged_files
      remaining_seconds = elapsed * remaining_files / self.merged_files
      self.eta_deadline = current_time + remaining_seconds
      self.eta_expired = remaining_seconds < 0.5
      self._print_progress(current_time)

  def finish(self, succeeded):
    self.stop_event.set()
    if self.refresh_thread is not None:
      self.refresh_thread.join()
    elapsed = time.monotonic() - self.start_time
    info("\033[0m")
    if succeeded:
      info(f"Merge finished in {format_duration(elapsed)}")


def skip_files_without_keys(file_paths):
  import ROOT

  files_with_keys = []
  skipped_files = []
  uninspected_files = []
  total_files = len(file_paths)
  start_time = time.monotonic()
  previous_error_level = ROOT.gErrorIgnoreLevel
  ROOT.gErrorIgnoreLevel = ROOT.kError
  info(f"Checking {total_files} input ROOT files for keys...")
  if total_files:
    print_file_progress(0, total_files)

  try:
    for file_index, file_path in enumerate(file_paths, start=1):
      try:
        input_file = ROOT.TFile.Open(file_path, "READ")
      except OSError:
        input_file = None
      if not input_file or input_file.IsZombie():
        if input_file:
          input_file.Close()
        files_with_keys.append(file_path)
        uninspected_files.append(file_path)
      else:
        if input_file.GetNkeys() == 0:
          skipped_files.append(file_path)
        else:
          files_with_keys.append(file_path)
        input_file.Close()

      print_file_progress(file_index, total_files)
  finally:
    ROOT.gErrorIgnoreLevel = previous_error_level
    if total_files:
      info("\033[0m")
  for file_path in uninspected_files:
    info(f"Could not inspect ROOT keys; leaving file for hadd to handle: {file_path}")
  for file_path in skipped_files:
    info(f"Skipping ROOT file with no keys: {file_path}")
  elapsed = time.monotonic() - start_time
  info(
    f"Key check finished in {elapsed:.1f} s: "
    f"kept {len(files_with_keys)} files and skipped {len(skipped_files)} files"
  )
  return files_with_keys


def build_hadd_command(
  output_file,
  input_files,
  preserve_input_compression,
  hadd_files_per_pass=None,
  hadd_workers=4,
):
  force_option = "-fk" if preserve_input_compression else "-f"
  command = ["hadd", force_option]
  if hadd_workers > 1:
    command.extend(["-j", str(hadd_workers)])
  command.extend(["-k", "-v", "99"])
  if hadd_files_per_pass is not None:
    # hadd's -n limit includes the target file itself.
    command.extend(["-n", str(hadd_files_per_pass + 1)])
  return [*command, output_file, *input_files]


def run_command(command):
  subprocess.run(command, check=True)


def run_hadd(
  command,
  input_files,
  merge_progress,
  hadd_files_per_pass=None,
  show_hadd_output=False,
):
  process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
  )
  output_lines = []
  pending_batch_sizes = []
  completed_files = 0

  for output_line in process.stdout:
    output_lines.append(output_line)
    # "Source file" messages are emitted while hadd opens inputs, before the
    # expensive merge. An "Opening the next"/"Target path" pair marks a real
    # internal pass boundary, so only those events may advance live progress.
    opening_match = re.search(r"hadd Opening the next (\d+) files", output_line)
    if opening_match:
      if hadd_files_per_pass is None:
        pending_batch_sizes.append(int(opening_match.group(1)))
      else:
        max_reportable_files = max(0, len(input_files) - 1)
        completed_batch_size = min(
          hadd_files_per_pass,
          max_reportable_files - completed_files,
        )
        completed_files += completed_batch_size
        merge_progress.advance(completed_batch_size)
    elif "hadd Target path:" in output_line and pending_batch_sizes:
      announced_batch_size = pending_batch_sizes.pop(0)
      max_reportable_files = max(0, len(input_files) - 1)
      completed_batch_size = min(
        announced_batch_size,
        max_reportable_files - completed_files,
      )
      completed_files += completed_batch_size
      merge_progress.advance(completed_batch_size)

    if show_hadd_output:
      merge_progress.print_message(output_line)

  return_code = process.wait()
  if return_code != 0:
    if show_hadd_output:
      raise RuntimeError(f"hadd failed with exit code {return_code}; captured output was shown above")
    output = "".join(output_lines)
    raise RuntimeError(f"hadd failed with exit code {return_code}. Captured output:\n{output}")

  merge_progress.advance(len(input_files) - completed_files)


def write_file(path, content):
  with open(path, "w", encoding="utf-8") as output_file:
    output_file.write(content)


def get_merge_targets(files_config):
  targets = []

  if hasattr(files_config, "output_hists_dir"):
    targets.append(("histograms", files_config.output_hists_dir))

  if hasattr(files_config, "output_trees_dir"):
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
):
  jobs = []
  info(f"[{merge_kind}] base dir: {base_dir}")

  for sample in samples:
    input_dir = build_sample_dir(base_dir, sample)
    input_pattern = os.path.join(input_dir, "*.root")
    output_dir = f"{input_dir}_merged"

    info(f"[{merge_kind}] sample: {sample}")
    info(f"[{merge_kind}] deduced input dir: {input_dir}")
    info(f"[{merge_kind}] deduced input pattern: {input_pattern}")
    info(f"[{merge_kind}] deduced output dir: {output_dir}")

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
  show_hadd_output,
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

  script_content = "\n".join([
    "#!/bin/bash",
    "set -e",
    "touch condor_dummy.out",
    f"mkdir -p {shlex.quote(os.path.dirname(output_file))}",
    shlex.join(hadd_command),
    "",
  ])
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
    submit_lines.extend([
      "should_transfer_files = YES",
      "when_to_transfer_output = ON_EXIT",
      "transfer_output_files = condor_dummy.out",
    ])
  else:
    submit_lines.append("should_transfer_files = NO")

  submit_lines.extend([
    "queue script from (",
    *executable_paths,
    ")",
    "",
  ])

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
):
  for _, _, _, _, output_dir, output_file, input_files in merge_jobs:
    os.makedirs(output_dir, exist_ok=True)
    command = build_hadd_command(
      output_file,
      input_files,
      preserve_input_compression,
      hadd_files_per_pass,
      hadd_workers,
    )
    run_hadd(
      command,
      input_files,
      merge_progress,
      hadd_files_per_pass,
      show_hadd_output,
    )


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
  merge_targets = get_merge_targets(files_config)
  if not merge_targets:
    raise ValueError("files_config must define output_hists_dir and/or output_trees_dir")

  jobs_by_kind = []
  for merge_kind, base_dir in merge_targets:
    jobs = collect_jobs(
      samples,
      base_dir,
      merge_kind,
      args.n_files_to_merge,
      provenance_tag,
      args.skip_no_keys,
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

  merge_progress = MergeProgress(sum(len(job[-1]) for job in jobs))
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
