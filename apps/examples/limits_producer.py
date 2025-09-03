import ROOT
import argparse
import importlib
import os
import concurrent.futures
import subprocess
import time
import re

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


def run_combine(config, datacard_file_names):
  base_command = (
      f'cd {config.combine_path}; '
      f'cmssw-el7 --no-home --command-to-run \"cmsenv; '
      f'cd {config.datacards_output_path};'
  )
  # Test cmssw-el7
  test_command = f"{base_command} echo \"\""
  if subprocess.run(test_command, shell=True).returncode != 0:
      base_command = (
      f'cd {config.combine_path}; '
      f'cmssw-el9 --no-home --command-to-run \"cmsenv; '
      f'cd {config.datacards_output_path};'
  )
  commands = []

  for datacard_file_name in datacard_file_names:
    datacard_path = config.datacards_output_path + datacard_file_name + ".txt"
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
