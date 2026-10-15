#!/usr/bin/env python3
import ROOT
import argparse
import importlib
import os
import concurrent.futures
import subprocess
import time
import re
import shlex
import math
from pathlib import Path

from HistogramsManager import HistogramsManager
from Logger import fatal, info, error, logger_print

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="", help="Path to the config file.")
parser.add_argument("--condor", action="store_true", help="Run in condor mode.")
parser.add_argument("--method", type=str, default="AsymptoticLimits", help="Combine method to use.")
args = None


def get_file(sample):
  try:
    file = ROOT.TFile.Open(sample.file_path, "READ")
  except OSError:
    fatal(f"Couldn't open file {sample.file_path}")
    exit(1)
  return file


def get_datacard_file_name(config, signal_sample):
  if getattr(config, "use_combined_limits", False):
    match = re.search(r"mAlp-([0-9p.]+)GeV_ctau-([0-9eE.+-]+)mm", signal_sample.name)
    mass = 0
    ctau = 0
    if match:
      mass = match.group(1)
      ctau = match.group(2)
    datacard_path = f"combined_datacard_{mass}_{ctau}{config.category}"
  else:
    datacard_path = f"datacard_{config.histogram.getName()}_{signal_sample.name}"
    if hasattr(config, "do_abcd") and config.do_abcd:
      datacard_path += "_ABCD"
      if config.use_abcd_prediction:
        datacard_path += "pred"
      else:
        datacard_path += "real"
  return datacard_path


def run_command(command):
  return subprocess.run(command, shell=True, executable="/bin/bash").returncode


def run_commands_in_parallel(commands, max_workers=None):
  info("Running all processes...")
  with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(run_command, cmd) for cmd in commands]

    # Wait for all commands to complete
    for future in concurrent.futures.as_completed(futures):
      returncode = future.result()
      if returncode != 0:
        raise RuntimeError(f"Combine command failed with exit status {returncode}")
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
    f.write("RequestMemory = 1000MB\n")
    f.write("Initialdir = .\n")
    f.write("GetEnv = True\n")
    f.write('+JobFlavour = "espresso"\n')
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
    f"source /cvmfs/cms.cern.ch/cmsset_default.sh && cd {shlex.quote(str(combine_path))} && eval \"$(scram runtime -sh)\"",
    f"cd {shlex.quote(str(combine_path))} && cmsenv",
    f"cd {shlex.quote(str(combine_path))} && source env_lcg.sh",
    f"cd {shlex.quote(str(combine_path))} && cmssw-el9 --no-home --command-to-run cmsenv",
    f"cd {shlex.quote(str(combine_path))} && cmssw-el7 --no-home --command-to-run cmsenv",
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


def run_combine(config, datacard_file_names, method=None):
  original_dir = Path.cwd()
  datacards_dir = (original_dir / config.datacards_output_path).resolve()
  method = method or (args.method if args is not None else "AsymptoticLimits")
  options = shlex.join(str(option) for option in getattr(config, "combine_options", ()))
  preload = getattr(config, "combine_preload_path", None)
  combine_command = "combine"
  if preload:
    preload_path = Path(preload).resolve()
    if not preload_path.is_file():
      raise FileNotFoundError(f"Combine preload library is missing: {preload_path}")
    loader = Path(getattr(config, "combine_loader_path", "/lib64/ld-linux-x86-64.so.2"))
    if not loader.is_file():
      raise FileNotFoundError(f"Combine dynamic loader is missing: {loader}")
    # LD_PRELOAD is inherited by ROOT's helper programs and can recursively
    # initialize ROOT in them. --preload affects only this Combine process.
    combine_command = (shlex.quote(str(loader)) + " --preload " +
                       shlex.quote(str(preload_path)) + ' "$(command -v combine)"')

  commands = []
  combine_setup = find_combine(config)
  for name in datacard_file_names:
    datacard_path = datacards_dir / f"{name}.txt"
    combine_log = datacard_path.with_suffix(".log")
    card_options = shlex.join(str(option) for option in getattr(config, "combine_options_by_datacard", {}).get(name, ()))

    cmd = "bash -lc " + shlex.quote(
      "set -e -o pipefail; "
      f"{combine_setup}; "
      f"cd {shlex.quote(str(datacards_dir))}; "
      f"{combine_command} -M {shlex.quote(method)} {shlex.quote(str(datacard_path))} "
      f"-n {shlex.quote('.' + name)} {options} {card_options} "
      f"> {shlex.quote(str(combine_log))} 2>&1"
    )
    commands.append(cmd)

  # Dispatch (your helpers should execute shell strings and honor non-zero exits)
  if getattr(config, "condor", False) or (globals().get("args") and getattr(args, "condor", False)):
    info("Running commands with condor...")
    run_commands_with_condor(commands)
  else:
    workers = getattr(config, "combine_max_workers", None)
    if workers == 1:
      info("Running commands sequentially...")
      for command in commands:
        returncode = run_command(command)
        if returncode != 0:
          raise RuntimeError(f"Combine command failed with exit status {returncode}")
    else:
      info("Running commands in parallel...")
      run_commands_in_parallel(commands, workers)


def read_limit_quantiles(file_path):
  """Read Combine quantiles without relying on the order of its log lines."""
  quantiles = {"observed": None, "minus2": None, "minus1": None,
               "median": None, "plus1": None, "plus2": None}
  expected = {0.025: "minus2", 0.16: "minus1", 0.5: "median", 0.84: "plus1", 0.975: "plus2"}
  root_file = ROOT.TFile.Open(str(file_path), "READ")
  if not root_file or root_file.IsZombie():
    raise RuntimeError(f"Unreadable Combine output: {file_path}")
  try:
    tree = root_file.Get("limit")
    if not tree:
      raise RuntimeError(f"Missing limit tree: {file_path}")
    for entry in tree:
      quantile = float(entry.quantileExpected)
      if quantile < 0:
        quantiles["observed"] = float(entry.limit)
      else:
        for target, key in expected.items():
          if abs(quantile - target) < 1.e-3:
            quantiles[key] = float(entry.limit)
            break
  finally:
    root_file.Close()
  if any(quantiles[key] is None for key in expected.values()):
    raise RuntimeError(f"Incomplete expected quantiles in {file_path}: {quantiles}")
  values = [quantiles[key] for key in expected.values()]
  if any(not math.isfinite(value) or value <= 0 for value in values) or values != sorted(values):
    raise RuntimeError(f"Invalid expected quantiles in {file_path}: {quantiles}")
  return quantiles


def get_limits(config):
  limits_per_process = {}

  for signal_sample in config.signal_samples:
    name = get_datacard_file_name(config, signal_sample)
    root_path = Path(config.datacards_output_path) / f"higgsCombine.{name}.AsymptoticLimits.mH120.root"
    if root_path.exists():
      quantiles = read_limit_quantiles(root_path)
      limits_per_process[signal_sample.name] = list(quantiles.values())
      continue
    combine_output_path = name + ".log"

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

  os.makedirs(config.results_output_path, exist_ok=True)

  with open(f"{config.results_output_path}/{file_path}", "w") as limits_file:
    for signal_name, limits in limits_per_process.items():
      limits_file.write(f"{signal_name}: {limits}\n")
      info(f"{signal_name}: {limits}")


def print_significance(config):
  for data_sample in config.data_samples:
    combine_output_path = get_datacard_file_name(config, data_sample) + ".log"

    try:
      with open(f"{config.datacards_output_path}/{combine_output_path}", "r") as combine_output_file:
        combine_output = combine_output_file.read()
        significance_lines = [line for line in combine_output.split("\n") if "Significance:" in line]
        if significance_lines:
          significance = significance_lines[-1].split("Significance:")[1].strip()
          info(f"Significance for {data_sample.name}: {significance}")
        else:
          error(f"No significance found in {combine_output_path}")
    except FileNotFoundError:
      error(f"File {combine_output_path} not found.")
      continue


def main():
  global args
  args = parser.parse_args()
  ROOT.gROOT.SetBatch(True)

  config = importlib.import_module(args.config.replace(".py", "").replace("/", "."))

  input_files = {}
  datacard_file_names = []

  signal_samples = config.signal_samples if hasattr(config, "signal_samples") else []
  data_samples = config.data_samples if hasattr(config, "data_samples") else []
  background_samples = config.background_samples if hasattr(config, "background_samples") else []

  for signal_sample in signal_samples:
    input_files[signal_sample.name] = get_file(signal_sample)

  for background_sample in background_samples:
    input_files[background_sample.name] = get_file(background_sample)

  for data_sample in data_samples:
    input_files[data_sample.name] = get_file(data_sample)

  main_samples = signal_samples if args.method == "AsymptoticLimits" else data_samples
  other_samples = background_samples + (data_samples if args.method == "AsymptoticLimits" else signal_samples)

  for main_sample in main_samples:
    datacard_file_name = get_datacard_file_name(config, main_sample)

    info(f"Creating HistogramsManager for {datacard_file_name}")

    manager = HistogramsManager(config, input_files, datacard_file_name)
    manager.addHistosample(config.histogram, main_sample)

    for other_sample in other_samples:
      manager.addHistosample(config.histogram, other_sample)

    manager.normalizeHistograms()
    manager.buildStacks()
    manager.saveDatacards()
    datacard_file_names.append(datacard_file_name)

  if not config.skip_combine:
    run_combine(config, datacard_file_names)

  if args.method == "AsymptoticLimits":
    save_limits(config)
  elif args.method == "Significance":
    print_significance(config)

  logger_print()


if __name__ == "__main__":
  main()
