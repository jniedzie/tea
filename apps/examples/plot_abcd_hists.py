import ROOT
import importlib
import sys

from ABCDPlotter import ABCDPlotter


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

    abcdPlotter.plot_optimization_hists()
    abcdPlotter.plot_per_signal_hists()
    abcdPlotter.plot_and_save_best_abcd_points()

    abcdPlotter.plot_background_projections()
    abcdPlotter.plot_signal_projections()
    abcdPlotter.plot_projections_ratio()

    abcdPlotter.save_canvases()
    abcdPlotter.print_params_for_selected_point()


if __name__ == "__main__":
    main()
