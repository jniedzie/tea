from HistogramPlotter import HistogramPlotter
from Logger import error, logger_print

import ROOT
import importlib
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="", help="Path to the config file.")
args = parser.parse_args()


def main():
  ROOT.gROOT.SetBatch(True)

  config = importlib.import_module(args.config.replace(".py", "").replace("/", "."))
  plotter = HistogramPlotter(config)

  input_files = {}

  for sample in config.samples:
    try:
      input_files[sample.name] = ROOT.TFile.Open(sample.file_path, "READ")
    except OSError:
      error(f"File {sample.file_path} not found!")
      continue

    for hist in config.histograms:
      plotter.addHistosample(hist, sample, input_files[sample.name])

    if hasattr(config, "histograms2D"):
      for hist in config.histograms2D:
        plotter.addHistosample2D(hist, sample, input_files[sample.name])

    if hasattr(config, "histogramsRatio"):
      for histpair in config.histogramsRatio:
        plotter.addHistosampleRatio(
          histpair[0], histpair[1], sample, input_files[sample.name]
        )

  plotter.setupLegends()
  plotter.buildStacks()
  plotter.buildStacksRatio()
  if sample.name in input_files:
    plotter.addHists2D(input_files[sample.name], sample)
  plotter.drawStacks()
  plotter.drawRatioStacks()
  plotter.drawHists2D()

  logger_print()


if __name__ == "__main__":
  main()
