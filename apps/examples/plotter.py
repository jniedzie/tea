#!/usr/bin/env python3
from Logger import error, info, info_frame, logger_print, ProgressBar
import importlib
import argparse
import os


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--config", type=str, default="", help="Path to the config file.")
  args = parser.parse_args()

  # ROOT initializes lazily when the plotting classes are first accessed.
  # Announce it first, and select batch mode before importing those classes.
  info("Initializing ROOT...")
  import ROOT
  ROOT.gROOT.SetBatch(True)
  from HistogramPlotter import HistogramPlotter

  info(f"Loading plotting configuration: {args.config}")
  config = importlib.import_module(args.config.replace(".py", "").replace("/", "."))
  plotter = HistogramPlotter(config)

  # HistogramNormalizer has already opened these files to read cutFlow.  Reuse
  # those handles instead of reopening every remote ROOT file.
  input_files = dict(plotter.normalizer.input_files)
  histograms2D = getattr(config, "histograms2D", [])
  histogramsRatio = getattr(config, "histogramsRatio", [])
  steps_per_sample = 1 + len(config.histograms) + len(histograms2D) + len(histogramsRatio)
  completed = 0
  last_valid_sample = None

  with ProgressBar(len(config.samples) * steps_per_sample, label="Loading histograms") as progress:
    for sample in config.samples:
      progress.update(completed, sample.name)
      if sample.name not in input_files:
        try:
          input_files[sample.name] = ROOT.TFile.Open(sample.file_path, "READ")
        except OSError:
          error(f"File {sample.file_path} not found!")
          completed += steps_per_sample
          progress.update(completed, sample.name)
          continue

      input_file = input_files[sample.name]
      if not input_file or input_file.IsZombie():
        error(f"File {sample.file_path} could not be opened!")
        completed += steps_per_sample
        progress.update(completed, sample.name)
        continue
      last_valid_sample = sample
      completed += 1
      progress.update(completed, sample.name)

      for hist in config.histograms:
        plotter.addHistosample(hist, sample, input_file)
        completed += 1
        progress.update(completed, f"{sample.name}: {hist.getName()}")

      for hist in histograms2D:
        plotter.addHistosample2D(hist, sample, input_file)
        completed += 1
        progress.update(completed, f"{sample.name}: {hist.getName()}")

      for histpair in histogramsRatio:
        plotter.addHistosampleRatio(histpair[0], histpair[1], sample, input_file)
        completed += 1
        progress.update(completed, f"{sample.name}: {histpair[0].getName()}")

  info("Preparing legends...")
  plotter.setupLegends()
  info("Building histogram stacks...")
  plotter.buildStacks()
  info("Building ratio stacks...")
  plotter.buildStacksRatio()
  if last_valid_sample is not None:
    plotter.addHists2D(input_files[last_valid_sample.name], last_valid_sample)
  plotter.drawStacks()
  plotter.drawRatioStacks()
  plotter.drawHists2D()

  logger_print()
  info_frame(f"Plots were saved to:\n{os.path.abspath(config.output_path)}")


if __name__ == "__main__":
  main()
