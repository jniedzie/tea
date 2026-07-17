#!/usr/bin/env python3
import argparse
import concurrent.futures
import glob
import importlib.util
import os
import shlex
import subprocess
import sys

from Logger import info
from teaHelpers import get_facility


def parse_args():
  parser = argparse.ArgumentParser(description="Merge ROOT files in batches of N.")
  parser.add_argument("--files_config", required=True, help="Path to the files config.")
  parser.add_argument(
    "-n",
    "--n-files-to-merge",
    type=int,
    default=20,
    help="Number of input files per merged output.",
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
  return parser.parse_args()


def load_files_config(config_path):
  spec = importlib.util.spec_from_file_location("files_config", config_path)
  files_config = importlib.util.module_from_spec(spec)
  sys.modules["files_config"] = files_config
  spec.loader.exec_module(files_config)
  return files_config


def chunk_files(file_paths, chunk_size):
  return [file_paths[index:index + chunk_size] for index in range(0, len(file_paths), chunk_size)]


def run_command(command):
  info(f"Running command: {shlex.join(command)}")
  subprocess.run(command, check=True)


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


def collect_jobs(samples, base_dir, merge_kind, chunk_size):
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

    for batch_index, batch_files in enumerate(chunk_files(input_files, chunk_size)):
      output_file = os.path.join(output_dir, f"ntuple_{batch_index}.root")
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
    info(f"    command: {shlex.join(['hadd', '-f', '-j', '-k', output_file, *input_files])}")


def create_condor_job(condor_dir, merge_kind, sample, batch_index, output_file, input_files):
  safe_sample = sample.replace("/", "_")
  script_path = os.path.join(condor_dir, f"{merge_kind}_{safe_sample}_{batch_index}.sh")
  quoted_inputs = " ".join(shlex.quote(path) for path in input_files)
  quoted_output = shlex.quote(output_file)

  script_content = "\n".join([
    "#!/bin/bash",
    "set -e",
    "touch condor_dummy.out",
    f"mkdir -p {shlex.quote(os.path.dirname(output_file))}",
    f"hadd -f -j -k {quoted_output} {quoted_inputs}",
    "",
  ])
  write_file(script_path, script_content)
  os.chmod(script_path, 0o755)
  return script_path


def submit_condor_jobs(condor_dir, jobs):
  os.makedirs(condor_dir, exist_ok=True)
  facility = get_facility()

  executable_paths = [
    create_condor_job(condor_dir, merge_kind, sample, batch_index, output_file, input_files)
    for merge_kind, sample, batch_index, _, _, output_file, input_files in jobs
  ]

  submit_lines = [
    "universe = vanilla",
    "getenv = True",
    "executable = $(script)",
    f"log = {condor_dir}/$(ClusterId).$(ProcId).log",
    f"output = {condor_dir}/$(ClusterId).$(ProcId).out",
    f"error = {condor_dir}/$(ClusterId).$(ProcId).err",
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


def run_jobs_locally(merge_jobs):
  for _, _, _, _, output_dir, output_file, input_files in merge_jobs:
    os.makedirs(output_dir, exist_ok=True)
    run_command(["hadd", "-f", "-j", "-k", output_file, *input_files])


def main():
  args = parse_args()
  if args.n_files_to_merge <= 0:
    raise ValueError("--n-files-to-merge must be greater than 0")

  files_config = load_files_config(args.files_config)
  samples = files_config.samples
  merge_targets = get_merge_targets(files_config)
  if not merge_targets:
    raise ValueError("files_config must define output_hists_dir and/or output_trees_dir")

  jobs_by_kind = []
  for merge_kind, base_dir in merge_targets:
    jobs = collect_jobs(samples, base_dir, merge_kind, args.n_files_to_merge)
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
      submit_condor_jobs(os.path.join(condor_base_dir, merge_kind), merge_jobs)
    return

  with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs_by_kind)) as executor:
    futures = [executor.submit(run_jobs_locally, merge_jobs) for _, _, merge_jobs in jobs_by_kind]
    for future in futures:
      future.result()


if __name__ == "__main__":
  main()
