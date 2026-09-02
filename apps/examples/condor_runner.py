#!/usr/bin/env python3
"""Run one app instance on a worker node (or one slot of --local_parallel).

On a real condor worker the app writes its outputs into _CONDOR_SCRATCH_DIR and this
script publishes them to their final (often dCache/EOS) destination only after the app
exits successfully: writing straight to a heavily-contended network mount intermittently
corrupts ROOT files mid-write. Only --output_hists_path and --output_trees_path are
redirected this way, so an app that writes a third output from a config key of its own
still writes it straight to the mount.
"""

from Logger import error, info, warn

import argparse
import ast
import os
import shlex
import subprocess
import sys

from teaHelpers import begin_stage_budget, stage_output, stage_preflight, validate_root_file


def get_args():
  parser = argparse.ArgumentParser(description="Submitter")

  parser.add_argument("--app", type=str, help="name of the app to run", required=True)
  parser.add_argument("--config", type=str, default="", help="config to be executred by the app")
  parser.add_argument("--file_index", type=int, help="index of the file from the DAS dataset to run on", required=True)
  parser.add_argument("--input_files_file_name", type=str, default="", help="path to a file with input files")
  parser.add_argument("--output_trees_dir", type=str, default="", help="output trees path")
  parser.add_argument("--output_hists_dir", type=str, default="", help="output hists path")
  parser.add_argument("--file_name", type=str, default="", help="name of a file from the DAS dataset to run on")
  parser.add_argument(
    "--facility",
    type=str,
    default="default",
    help="facility this job was submitted from, used to pick the stage-out transport",
  )

  args, unknown = parser.parse_known_args()
  return args, unknown


def try_parse_tuple(s):
  try:
    return ast.literal_eval(s)
  except (ValueError, SyntaxError):
    return s


def main():
  # hack the xauth issue
  os.system('echo "export DISPLAY=${DISPLAY}" > ${JOB_WORKING_DIR}/.display')
  os.system('echo "export TERM=${TERM}" >> ${JOB_WORKING_DIR}/.display')
  os.system("export XAUTHORITY=${JOB_WORKING_DIR}/.Xauthority")
  os.system('/usr/bin/xauth "$@" </dev/stdin')

  args, extra_args = get_args()
  app_name = args.app
  executor = "python3 " if app_name[-3:] == ".py" else "./"
  command = f"{executor}{app_name} --config {args.config}"

  input_files = open(args.input_files_file_name).read().splitlines()
  input_file_path = input_files[args.file_index]
  input_file_path = try_parse_tuple(input_file_path)

  output_tree_path = None
  output_hist_path = None

  if isinstance(input_file_path, tuple):
    input_file_path, output_tree_path, output_hist_path = input_file_path

  if args.file_name != "":
    input_file_name = args.file_name
    path = "/".join(input_file_path.strip().split("/")[:-1])
    input_file_path = f"{path}/{input_file_name}"
  else:
    input_file_name = input_file_path.strip().split("/")[-1]

  # create output dir if doesn't exist -- exist_ok because ~1500 jobs racing to create the
  # same directory otherwise lose the check-then-act.
  if args.output_trees_dir != "":
    os.makedirs(args.output_trees_dir, exist_ok=True)
  if args.output_hists_dir != "":
    os.makedirs(args.output_hists_dir, exist_ok=True)

  output_trees_file_path = ""
  output_hists_file_path = ""

  if output_tree_path is not None:
    output_trees_file_path = output_tree_path
  elif args.output_trees_dir != "":
    output_trees_file_path = f"{args.output_trees_dir}/{input_file_name}"

  if output_hist_path is not None:
    output_hists_file_path = output_hist_path
  elif args.output_hists_dir != "":
    output_hists_file_path = f"{args.output_hists_dir}/{input_file_name}"

  # Captured before the flag-wrapping below overwrites these with "--output_..._path <path>".
  final_trees_path = output_trees_file_path
  final_hists_path = output_hists_file_path

  # Writing to local scratch and publishing afterwards is facility-independent; only the
  # copy protocol is site-specific, and that comes from --facility (resolved on the submit
  # node, where the hostname is actually recognizable). --local_parallel runs this same
  # script but never has _CONDOR_SCRATCH_DIR set, so it naturally falls through to the
  # untouched direct-write behavior.
  scratch_dir = os.environ.get("_CONDOR_SCRATCH_DIR", "")
  scratch_usable = bool(scratch_dir) and os.path.isdir(scratch_dir) and os.access(scratch_dir, os.W_OK)
  if scratch_dir and not scratch_usable:
    warn(
      f"_CONDOR_SCRATCH_DIR={scratch_dir} is set but not usable (missing or not "
      f"writable); writing outputs directly to their final paths"
    )
  use_scratch = scratch_usable

  if use_scratch:
    # Ask now, not after hours of computation: a job that cannot stage out its result
    # should write straight to the final paths instead of discarding the finished output.
    preflight_ok, preflight_reason = stage_preflight([final_trees_path, final_hists_path], args.facility)
    if preflight_ok:
      info(f"Stage-out pre-flight passed for facility '{args.facility}': {preflight_reason}")
    else:
      warn(
        f"Stage-out pre-flight failed for facility '{args.facility}': {preflight_reason}; "
        f"writing outputs directly to their final paths"
      )
      use_scratch = False

  staged_outputs = []

  if use_scratch:
    # Separate subdirectories per output kind: in the output_trees_dir/output_hists_dir
    # shape both paths share the same basename, which would collide in a flat scratch dir.
    if output_trees_file_path != "":
      trees_scratch_dir = os.path.join(scratch_dir, "trees")
      os.makedirs(trees_scratch_dir, exist_ok=True)
      output_trees_file_path = os.path.join(trees_scratch_dir, os.path.basename(final_trees_path))
      staged_outputs.append((output_trees_file_path, final_trees_path))

    if output_hists_file_path != "":
      hists_scratch_dir = os.path.join(scratch_dir, "hists")
      os.makedirs(hists_scratch_dir, exist_ok=True)
      output_hists_file_path = os.path.join(hists_scratch_dir, os.path.basename(final_hists_path))
      staged_outputs.append((output_hists_file_path, final_hists_path))

  if output_trees_file_path != "":
    output_trees_file_path = f"--output_trees_path {output_trees_file_path}"
  if output_hists_file_path != "":
    output_hists_file_path = f"--output_hists_path {output_hists_file_path}"

  args_dict = {}
  for i in range(0, len(extra_args), 2):
    args_dict[extra_args[i]] = extra_args[i + 1]

  extra_args = " ".join([f"{key} {value}" for key, value in args_dict.items()])

  command_for_file = (
    f"{command} --input_path {input_file_path} {output_trees_file_path} {output_hists_file_path} {extra_args}"
  )
  command_args = shlex.split(command_for_file)

  # Log the argument vector that is actually executed: shlex.split drops the quoting the
  # string form still carries, so the string is not what ran.
  info(f"\n\nExecuting {command_args=}")
  result = subprocess.run(command_args, check=False)
  returncode = result.returncode

  if returncode == 0 and staged_outputs:
    # One wall-clock budget for every output of this job, so trees + hists cannot compound
    # their retries into a wall-time kill.
    begin_stage_budget()
    published = []
    failed = []
    for scratch_path, final_path in staged_outputs:
      try:
        validate_root_file(scratch_path)
        stage_output(scratch_path, final_path, args.facility)
        published.append(final_path)
      except Exception as exception:
        # No direct-write fallback: writing the file to the final path after a failed
        # transport is exactly the partially-written-output bug staging exists to avoid.
        failed.append(final_path)
        error(f"Failed to stage {scratch_path} -> {final_path}: {exception}")
        returncode = 1

    if failed:
      published_str = ", ".join(published) if published else "none"
      error(f"Stage-out failed for: {', '.join(failed)} (outputs that did land: {published_str})")

  sys.exit(returncode)


if __name__ == "__main__":
  main()
