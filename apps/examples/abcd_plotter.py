import ROOT
import importlib
import sys
import argparse

from ABCDPlotter import ABCDPlotter

parser = argparse.ArgumentParser()
parser.add_argument("--max_correlation", type=float, default=1.0, help="Max correlation for the background histograms.")
parser.add_argument("--min_signals", type=int, default=0,
                    help="Min number of signals for which optimal binning has to be found.")
args = parser.parse_args()


def getConfig():
  configPath = sys.argv[1]
  if (".py" in configPath):
    configPath = configPath[:-3]
  config = importlib.import_module(configPath)
  return config


def main():
  ROOT.gStyle.SetOptStat(0)
  ROOT.gROOT.SetBatch(True)

  config = getConfig()
  abcdPlotter = ABCDPlotter(config)

  correlation = abcdPlotter.plot_background_hist()

  if abs(correlation) > args.max_correlation:
    print("Correlation is too high, skipping the signal plots")
    return

  n_points_found = abcdPlotter.plot_and_save_best_abcd_points()

  if n_points_found < args.min_signals:
    print("Too few optimal points found, skipping the signal plots.")
    return

  abcdPlotter.plot_optimization_hists()
  abcdPlotter.plot_per_signal_hists()

  abcdPlotter.plot_background_projections()
  abcdPlotter.plot_signal_projections()
  abcdPlotter.plot_projections_ratio()
  abcdPlotter.plot_and_save_best_abcd_points()

  abcdPlotter.save_canvases()
  abcdPlotter.print_params_for_selected_point()
  abcdPlotter.plot_optimal_points()


if __name__ == "__main__":
  main()
