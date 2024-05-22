from Logger import *

import argparse
import os
import sys

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

def main():
  # hack the xauth issue
  os.system('echo "export DISPLAY=${DISPLAY}" > ${JOB_WORKING_DIR}/.display')
  os.system('echo "export TERM=${TERM}" >> ${JOB_WORKING_DIR}/.display')
  os.system('export XAUTHORITY=${JOB_WORKING_DIR}/.Xauthority')
  os.system('/usr/bin/xauth "$@" </dev/stdin')

  args, extra_args = get_args()
  app_name = args.app
  executor = f"python3 " if app_name[-3:] == ".py" else f"./"
  command = f"{executor}{app_name} --config {args.config}"

  input_files = open(args.input_files_file_name).read().splitlines()
  input_file_path = input_files[args.file_index]

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
  if args.output_trees_dir != "":
    output_trees_file_path = f"--output_trees_path {args.output_trees_dir}/{input_file_name}"
  if args.output_hists_dir != "":
    output_hists_file_path = f"--output_hists_path {args.output_hists_dir}/{input_file_name}"
  
  args_dict = {}
  for i in range(0, len(extra_args), 2):
    args_dict[extra_args[i]] = extra_args[i+1]
  
  extra_args = " ".join([f"{key} {value}" for key, value in args_dict.items()])
  
  command_for_file = f"{command} --input_path {input_file_path} {output_trees_file_path} {output_hists_file_path} {extra_args}"

  info(f"\n\nExecuting {command_for_file=}")
  os.system(command_for_file)


if __name__ == "__main__":
  main()
