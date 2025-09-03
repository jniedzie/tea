import ROOT
import argparse
import importlib
import os
import concurrent.futures
import subprocess
import time
import re
import shlex
from pathlib import Path

from HistogramsManager import HistogramsManager
from Logger import fatal, info, error, logger_print

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="", help="Path to the config file.")
parser.add_argument("--condor", action="store_true", help="Run in condor mode.")
args = parser.parse_args()


def get_file(sample):
  try:
    file = ROOT.TFile.Open(sample.file_path, "READ")
  except OSError:
    fatal(f"Couldn't open file {sample.file_path}")
    exit(0)
  return file


def get_datacard_file_name(config, signal_sample):
  datacard_path = f"datacard_{config.histogram.getName()}_{signal_sample.name}"
  if hasattr(config, "do_abcd") and config.do_abcd:
    datacard_path += "_ABCD"
    if config.use_abcd_prediction:
      datacard_path += "pred"
    else:
      datacard_path += "real"
  return datacard_path


def run_command(command):
  return os.system(command)


def run_commands_in_parallel(commands):
  info("Running all processes...")
  with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(run_command, cmd) for cmd in commands]

    # Wait for all commands to complete
    for future in concurrent.futures.as_completed(futures):
      _ = future.result()
  info("All processes completed.")


def run_commands_with_condor(commands):
  submit_file = "run_limits.sub"

  os.makedirs("scripts", exist_ok=True)

  for i, command in enumerate(commands):
    with open(f"scripts/combine_job{i}.sh", "w") as f:
      f.write("#!/bin/bash\n")
      f.write(command + "\n")
      os.chmod(f"scripts/combine_job{i}.sh", 0o755)

  with open(submit_file, "w") as f:
    f.write("executable = scripts/combine_job$(Process).sh\n")
    f.write("output = output/$(Cluster).$(Process).out\n")
    f.write("error = error/$(Cluster).$(Process).err\n")
    f.write("log = log/$(Cluster).log\n")
    f.write("RequestCpus = 1\n")
    f.write("RequestMemory = 4000MB\n")
    f.write("Initialdir = .\n")
    f.write("GetEnv = True\n")
    f.write("+JobFlavour = \"espresso\"\n")
    f.write(f"queue {len(commands)}\n")

  submit_output = subprocess.check_output(["condor_submit", submit_file], text=True)
  print(submit_output)

  match = re.search(r"submitted to cluster (\d+)", submit_output)
  if not match:
    raise RuntimeError("Could not extract cluster ID")
  cluster_id = match.group(1)
  print(f"Submitted cluster ID: {cluster_id}")

  output = subprocess.check_output(["condor_q", cluster_id], text=True)
  lines = output.strip().split("\n")

  for line in lines:
    if line.startswith("OWNER"):
      print(line)
      break

  # Wait for jobs to finish
  while True:
    time.sleep(2)
    try:
      output = subprocess.check_output(["condor_q", cluster_id], text=True)
      job_line = next((line for line in output.splitlines() if cluster_id in line), None)
    except subprocess.CalledProcessError:
      job_line = None

    if job_line:
      print(f"\r{job_line:<120}", end="", flush=True)  # Pad to clear previous text
    else:
      print("\rJob finished.                                                        ")
      break

def find_combine(config):
  combine_path = Path(config.combine_path)  # should be CMSSW_X_Y_Z/src

  # Candidate environment setups (order matters). We verify that `combine` is available.
  setup_cmds = [
    f'cd {shlex.quote(str(combine_path))} && cmsenv',
    f'cd {shlex.quote(str(combine_path))} && source env_lcg.sh',
    f'cd {shlex.quote(str(combine_path))} && cmssw-el9 --no-home --command-to-run cmsenv',
    f'cd {shlex.quote(str(combine_path))} && cmssw-el7 --no-home --command-to-run cmsenv',
  ]

  # Pick the first working environment
  chosen_setup = None
  for setup in setup_cmds:
    test_cmd = f"set -e -o pipefail; {setup}; command -v combine >/dev/null 2>&1"
    print(f"Testing setup: {setup}")
    rc = subprocess.run(["bash", "-lc", test_cmd]).returncode
    if rc == 0:
      chosen_setup = setup
      break

  if not chosen_setup:
    fatal(f"Could not set up a working environment for Combine.\n")
    exit(1)
    
  return chosen_setup


def run_combine(config, datacard_file_names):
  original_dir = Path.cwd()
  datacards_dir = original_dir / config.datacards_output_path

  commands = []
  combine_setup = find_combine(config)
  for name in datacard_file_names:
    datacard_path = datacards_dir / f"{name}.txt"
    combine_log = datacard_path.with_suffix(".log")

    cmd = (
      "bash -lc "
      + shlex.quote(
        "set -e -o pipefail; "
        f"{combine_setup}; "
        f"cd {shlex.quote(str(datacards_dir))}; "
        f"combine -M AsymptoticLimits {shlex.quote(str(datacard_path))} "
        f"> {shlex.quote(str(combine_log))} 2>&1"
      )
    )
    commands.append(cmd)

  # Dispatch (your helpers should execute shell strings and honor non-zero exits)
  if getattr(config, "condor", False) or (globals().get("args") and getattr(args, "condor", False)):
    info("Running commands with condor...")
    run_commands_with_condor(commands)
  else:
    info("Running commands in parallel...")
    run_commands_in_parallel(commands)


def get_limits(config):
  limits_per_process = {}

  for signal_sample in config.signal_samples:
    combine_output_path = get_datacard_file_name(config, signal_sample) + ".log"

    try:
      with open(f"{config.datacards_output_path}/{combine_output_path}", "r") as combine_output_file:
        combine_output = combine_output_file.read()
        r_values = [line.split("r < ")[1].strip() for line in combine_output.split("\n") if "r < " in line]
        limits_per_process[signal_sample.name] = r_values
    except FileNotFoundError:
      error(f"File {combine_output_path} not found.")
      continue

  return limits_per_process


def save_limits(config):
  limits_per_process = get_limits(config)

  file_path = f"limits_{config.histogram.getName()}"
  if hasattr(config, "do_abcd") and config.do_abcd:
    file_path += "_ABCD"
    if config.use_abcd_prediction:
      file_path += "pred"
    else:
      file_path += "real"

  file_path += ".txt"

  info(f"Saving limits to {file_path}")

  if not os.path.exists(os.path.dirname(config.results_output_path)):
    os.makedirs(os.path.dirname(config.results_output_path))

  with open(f"{config.results_output_path}/{file_path}", "w") as limits_file:
    for signal_name, limits in limits_per_process.items():
      limits_file.write(f"{signal_name}: {limits}\n")
      info(f"{signal_name}: {limits}")


def main():
  ROOT.gROOT.SetBatch(True)

  config = importlib.import_module(args.config.replace(".py", "").replace("/", "."))

  input_files = {}
  datacard_file_names = []

  for signal_sample in config.signal_samples:
    input_files[signal_sample.name] = get_file(signal_sample)

  for background_sample in config.background_samples:
    input_files[background_sample.name] = get_file(background_sample)

  for signal_sample in config.signal_samples:
    datacard_file_name = get_datacard_file_name(config, signal_sample)

    manager = HistogramsManager(config, input_files, datacard_file_name)
    manager.addHistosample(config.histogram, signal_sample)

    for background_sample in config.background_samples:
      manager.addHistosample(config.histogram, background_sample)

    manager.normalizeHistograms()
    manager.buildStacks()
    manager.saveDatacards()
    datacard_file_names.append(datacard_file_name)

  if not config.skip_combine:
    run_combine(config, datacard_file_names)

  save_limits(config)

  logger_print()


if __name__ == "__main__":
  main()
