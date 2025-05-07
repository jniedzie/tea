import argparse
import importlib.util
import uuid
import os
from SubmissionManager import SubmissionManager, SubmissionSystem

from Logger import info, fatal, logger_print


def get_args():
  parser = argparse.ArgumentParser(description="Submitter")

  parser.add_argument("--app", type=str, help="Name of the app to run.", required=True)
  parser.add_argument("--config", type=str, required=True, help="Config to be executed by the app.")
  parser.add_argument("--files_config", type=str, default=None, help="Python config with a list of input/output paths.")
  parser.add_argument("--local", action="store_true", default=False, help="Run locally.")
  parser.add_argument("--condor", action="store_true", default=False, help="Run on condor.")
  parser.add_argument("--save_logs", action="store_true", default=False, help="Save condor logs.")
  parser.add_argument("--job_flavour", type=str, default="espresso",
                      help=(
                          "Condor job flavour: espresso (20 min), microcentury (1h), longlunch (2h), workday (8h), "
                          "tomorrow (1d), testmatch (3d), nextweek (1w)."
                      )
                      )
  parser.add_argument("--resubmit_job", type=int, default=None, help="Resubmitt a specific job.")
  parser.add_argument("--memory", type=float, default=1.0, help="Requested memory in GB.")
  parser.add_argument("--max_materialize", type=int, default=5000,
                      help=(
                          "An overall limit on the number of jobs that can be materialized "
                          "in the condor_schedd at any one time."
                      )
                      )

  parser.add_argument("--dry", action="store_true", default=False, help="dry run, without submitting to condor")

  args = parser.parse_args()
  return args


def get_config(args):
  info(f"Reading config from path: {args.config}")
  spec = importlib.util.spec_from_file_location("files_module", args.config)
  config = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(config)
  return config


def get_files_config(args):
  info(f"Reading files config from path: {args.files_config}")
  spec = importlib.util.spec_from_file_location("files_module", args.files_config)
  files_config = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(files_config)
  return files_config


def update_config(path, key, value):
  with open(path, "r") as f:
    lines = f.readlines()
  with open(path, "w") as f:
    for line in lines:
      if line.strip().startswith(key.strip()):
        line = f"{key} {value}"
      f.write(line)


def prepare_tmp_files(args):
  hash_string = str(uuid.uuid4().hex[:6])
  tmp_config_path = f"tmp/config_{hash_string}.py"
  tmp_files_config_path = f"tmp/files_config_{hash_string}.py"

  info(f"Creating a temporary config: {tmp_config_path}\t and files config: {tmp_files_config_path}")
  os.system("mkdir -p tmp")
  os.system(f"cp {args.files_config} {tmp_files_config_path}")
  os.system(f"cp {args.config} {tmp_config_path}")

  return tmp_config_path, tmp_files_config_path


def main():
  args = get_args()

  submission_system = SubmissionSystem.unknown
  if args.local:
    submission_system = SubmissionSystem.local
  if args.condor:
    submission_system = SubmissionSystem.condor

  if submission_system == SubmissionSystem.unknown:
    fatal("Please select either --local or --condor")
    exit()

  files_config = get_files_config(args)
  applyScaleFactors = {}
  if hasattr(files_config, "applyScaleFactors"):
    applyScaleFactors = files_config.applyScaleFactors

  tmp_configs_paths = []

  if hasattr(files_config, "samples"):
    samples = files_config.samples

    for sample in samples:
      tmp_config_path, tmp_files_config_path = prepare_tmp_files(args)

      for name, applyPair in applyScaleFactors.items():
        applyDefault = applyPair[0]
        applyVariation = applyPair[1]
        update_config(tmp_config_path, f"  \"{name}\":", "(False, False),\n" if "collision" in sample else f"({applyDefault}, {applyVariation}),\n")
      update_config(tmp_files_config_path, "sample_path = ", f"\"{sample}\"\n")

      tmp_configs_paths.append((tmp_config_path, tmp_files_config_path))
  elif (
      hasattr(files_config, "datasets_and_output_trees_dirs") or
      hasattr(files_config, "datasets_and_output_hists_dirs")
  ):
    datasets_and_output_dirs = {}
    if hasattr(files_config, "datasets_and_output_trees_dirs"):
      datasets_and_output_dirs = files_config.datasets_and_output_trees_dirs
      output_dir_name = "output_trees_dir"
    elif hasattr(files_config, "datasets_and_output_hists_dirs"):
      datasets_and_output_dirs = files_config.datasets_and_output_hists_dirs
      output_dir_name = "output_hists_dir"

    for dataset, output_dir in datasets_and_output_dirs:
      tmp_config_path, tmp_files_config_path = prepare_tmp_files(args)

      for name, applyPair in applyScaleFactors.items():
        applyDefault = applyPair[0]
        applyVariation = applyPair[1]
        update_config(tmp_config_path, f"  \"{name}\":", "(False, False),\n" if "collision" in dataset else f"({applyDefault}, {applyVariation}),\n")

      update_config(tmp_files_config_path, "dataset = ", f"\"{dataset}\"\n")
      update_config(tmp_files_config_path, f"{output_dir_name} = ", f"\"{output_dir}\"\n")

      tmp_configs_paths.append((tmp_config_path, tmp_files_config_path))
  elif hasattr(files_config, "input_dasfiles_and_output_trees_dirs"):
    input_dasfiles_and_output_dirs = files_config.input_dasfiles_and_output_trees_dirs
    output_dir_name = "output_trees_dir"

    for input_dasfiles, output_dir in input_dasfiles_and_output_dirs:
      tmp_config_path, tmp_files_config_path = prepare_tmp_files(args)

      for name, applyPair in applyScaleFactors.items():
        applyDefault = applyPair[0]
        applyVariation = applyPair[1]
        update_config(tmp_config_path, f"  \"{name}\":", "(False, False),\n" if "collision" in sample else f"({applyDefault}, {applyVariation}),\n")

      update_config(tmp_files_config_path, "input_dasfiles = ", f"\"{input_dasfiles}\"\n")
      update_config(tmp_files_config_path, f"{output_dir_name} = ", f"\"{output_dir}\"\n")

      tmp_configs_paths.append((tmp_config_path, tmp_files_config_path))
  else:
    tmp_configs_paths.append((args.config, args.files_config))

  for config_path, files_config_path in tmp_configs_paths:
    submission_manager = SubmissionManager(submission_system, args.app, config_path, files_config_path)

    if submission_system == SubmissionSystem.local:
      submission_manager.run_locally()
    if submission_system == SubmissionSystem.condor:
      submission_manager.run_condor(args)

  logger_print()


if __name__ == "__main__":
  main()
