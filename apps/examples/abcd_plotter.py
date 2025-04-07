import ROOT
import importlib
import argparse

from ABCDPlotter import ABCDPlotter
from Logger import warn, logger_print

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="", help="Path to the config file.")
parser.add_argument("--max_correlation", type=float, default=1.0, help="Max correlation for the background histograms.")
parser.add_argument("--min_signals", type=int, default=0, help="Min number of ""good"" signals.")
parser.add_argument("--max_overlap", type=float, default=1.0, help="Max overlap between background and signal.")
parser.add_argument("--max_error", type=float, default=1.0, help="Max allowed error expressed in number of sigmas.")
parser.add_argument("--max_closure", type=float, default=0.20, help="Max allowed closure.")
parser.add_argument("--min_n_events", type=int, default=10, help="Min number of events in any of the ABCD bins.")
parser.add_argument("--max_signal_contamination", type=float, default=0.20, help="Max allowed signal contamination in any of the ABCD bins.")
args = parser.parse_args()


def getConfig(path):
  if (".py" in path):
    path = path[:-3]
  config = importlib.import_module(path)
  return config


def main():
  ROOT.gStyle.SetOptStat(0)
  ROOT.gROOT.SetBatch(True)

  config = getConfig(args.config)
  abcdPlotter = ABCDPlotter(config, args.max_error, args.max_closure, args.min_n_events, args.max_signal_contamination)

  correlation = abcdPlotter.plot_background_hist()

  if abs(correlation) > args.max_correlation:
    warn("Correlation is too high, skipping the signal plots")
    return

  n_points_found = abcdPlotter.get_n_signals_with_good_binning()

  if n_points_found < args.min_signals:
    warn("Too few optimal points found, skipping the signal plots.")
    return

  n_signals_overlap_below_threshold = abcdPlotter.get_n_signals_with_overlap_with_background_below(args.max_overlap)

  if n_signals_overlap_below_threshold < args.min_signals:
    warn("Too few signals with overlap below threshold, skipping the signal plots.")
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
  
  logger_print()


if __name__ == "__main__":
  main()
