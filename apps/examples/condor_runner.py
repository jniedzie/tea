#!/usr/bin/env python3
from Logger import info

import argparse
import os
import ast
from pathlib import Path
import shlex
import subprocess
import tempfile


def get_args():
  parser = argparse.ArgumentParser(description="Submitter")

  parser.add_argument("--app", type=str, help="name of the app to run", required=True)
  parser.add_argument("--config", type=str, default="", help="config to be executred by the app")
  parser.add_argument("--file_index", type=int, help="index of the file from the DAS dataset to run on", required=True)
  parser.add_argument("--input_files_file_name", type=str, default="", help="path to a file with input files")
  parser.add_argument("--output_trees_dir", type=str, default="", help="output trees path")
  parser.add_argument("--output_hists_dir", type=str, default="", help="output hists path")
  parser.add_argument("--file_name", type=str, default="", help="name of a file from the DAS dataset to run on")

  args, unknown = parser.parse_known_args()
  return args, unknown


def try_parse_tuple(s):
  try:
    return ast.literal_eval(s)
  except (ValueError, SyntaxError):
    return s


def eos_path(path):
  if path.startswith("/eos/home-"):
    _, _, home, user, rest = path.split("/", 4)
    return f"/eos/user/{home[-1]}/{user}/{rest}"
  return path if path.startswith("/eos/user/") else None


def execute(command):
  """Stage EOS input/output locally and return the application's real status."""
  with tempfile.TemporaryDirectory(prefix="tea_condor_") as temporary:
    scratch = Path(temporary)
    publications = []
    for flag in ("--input_path", "--output_trees_path", "--output_hists_path"):
      if flag not in command:
        continue
      index = command.index(flag) + 1
      remote = eos_path(command[index])
      if remote is None:
        continue
      local = scratch / (flag[2:] + ".root")
      if flag == "--input_path":
        subprocess.run(["xrdcp", "--silent", "--cksum", "adler32", "root://eosuser.cern.ch/" + remote,
                        str(local)], check=True, timeout=900)
      else:
        publications.append((local, remote))
      command[index] = str(local)
    result = subprocess.run(command, check=False)
    if result.returncode:
      return result.returncode
    for local, remote in publications:
      if not local.is_file():
        raise RuntimeError(f"Application did not produce requested output: {local}")
      subprocess.run(["xrdfs", "root://eosuser.cern.ch", "mkdir", "-p", str(Path(remote).parent)],
                     check=True, timeout=120)
      subprocess.run(["xrdcp", "--silent", "--posc", "--rm-bad-cksum", "--cksum", "adler32",
                      str(local), "root://eosuser.cern.ch/" + remote], check=True, timeout=900)
    return 0


def main():
  # hack the xauth issue
  job_working_dir = os.environ.get("JOB_WORKING_DIR")
  if job_working_dir:
    with open(f"{job_working_dir}/.display", "w") as display_file:
      display_file.write(f"export DISPLAY={os.environ.get('DISPLAY', '')}\n")
      display_file.write(f"export TERM={os.environ.get('TERM', '')}\n")
    os.environ["XAUTHORITY"] = f"{job_working_dir}/.Xauthority"
    subprocess.run(["/usr/bin/xauth"], stdin=subprocess.DEVNULL, check=False)

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

  # create output dir if doesn't exist
  if not os.path.exists(args.output_trees_dir) and args.output_trees_dir != "":
    os.makedirs(args.output_trees_dir)
  if not os.path.exists(args.output_hists_dir) and args.output_hists_dir != "":
    os.makedirs(args.output_hists_dir)

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

  info(f"\n\nExecuting {command_for_file=}")
  return execute(shlex.split(command_for_file))


if __name__ == "__main__":
  raise SystemExit(main())
