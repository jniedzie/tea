#!/usr/bin/env python3
"""Plot explicitly configured points or labeled JSON limit results."""

import argparse
from Logger import info, info_frame
from LimitConfig import load_config, plot_inputs, plot_paths


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--config", required=True, help="Configuration module or Python file")
  args = parser.parse_args()

  info("Initializing ROOT...")
  import ROOT

  ROOT.gROOT.SetBatch(True)
  from LimitPlotter import PlotOptions, plot_limits
  from PlotCanvas import save_canvas

  config = load_config(args.config)
  points = plot_inputs(config)
  paths = plot_paths(config)
  canvas = plot_limits(points, getattr(config, "plot_options", PlotOptions()), plot_config=config)
  try:
    for path in paths:
      save_canvas(canvas, path)
  finally:
    canvas.Close()
  info_frame("Limit plots were saved to:\n" + "\n".join(map(str, paths)))


if __name__ == "__main__":
  main()
