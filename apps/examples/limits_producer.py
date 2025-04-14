import ROOT
import argparse
import importlib
import os
import concurrent.futures
import subprocess
import time
import re

from HistogramsManager import HistogramsManager
from Logger import fatal, info

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


def get_datacard_path(config, signal_sample):
  datacard_path = f"{config.output_path}/datacard_{config.histogram.getName()}_{signal_sample.name}"
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
    f.write("RequestMemory = 512MB\n")
    f.write("Initialdir = .\n")
    f.write("GetEnv = True\n")
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


def run_combine(cmssw_path, output_paths):

  cwd = os.getcwd()
  base_command = f'cd {cmssw_path}; cmssw-el7 --command-to-run \"cmsenv; cd {cwd}/../datacards/;'
  commands = []

  for output_path in output_paths:
    datacard_path = os.path.basename(output_path) + ".txt"
    combine_output_path = datacard_path.replace('.txt', '.log')

    command = f'{base_command} combine -M AsymptoticLimits {datacard_path} > {combine_output_path} \"'
    commands.append(command)

  if args.condor:
    info("Running commands with condor...")
    run_commands_with_condor(commands)
  else:
    info("Running commands in parallel...")
    run_commands_in_parallel(commands)


def get_limits(config):
  limits_per_process = {}

  for signal_sample in config.signal_samples:
    combine_output_path = os.path.basename(get_datacard_path(config, signal_sample)) + ".log"

    with open(f"{config.output_path}/{combine_output_path}", "r") as combine_output_file:
      combine_output = combine_output_file.read()
      r_values = [line.split("r < ")[1].strip() for line in combine_output.split("\n") if "r < " in line]
      limits_per_process[signal_sample.name] = r_values

  return limits_per_process


def save_limits(config):
  limits_per_process = get_limits(config)

  file_path = f"limits_{config.histogram.getName()}.txt"
  info(f"Saving limits to {file_path}")

  with open(f"../datacards/{file_path}", "w") as limits_file:
    for signal_name, limits in limits_per_process.items():
      limits_file.write(f"{signal_name}: {limits}\n")
      info(f"{signal_name}: {limits}")


def main():
  ROOT.gROOT.SetBatch(True)

  config = importlib.import_module(args.config.replace(".py", "").replace("/", "."))

  input_files = {}
  output_paths = []

  for signal_sample in config.signal_samples:
    output_path = get_datacard_path(config, signal_sample)
    manager = HistogramsManager(config, output_path)

    input_files[signal_sample.name] = get_file(signal_sample)
    manager.addHistosample(config.histogram, signal_sample, input_files[signal_sample.name])

    for background_sample in config.background_samples:

      input_files[background_sample.name] = get_file(background_sample)
      manager.addHistosample(config.histogram, background_sample, input_files[background_sample.name])

    manager.buildStacks()
    manager.saveDatacards()
    output_paths.append(output_path)

  if not config.skip_combine:
    run_combine(config.combine_path, output_paths)

  save_limits(config)


if __name__ == "__main__":
  main()
