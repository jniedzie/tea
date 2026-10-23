#!/usr/bin/env python3
"""Produce datacards and labeled limits, or evaluate existing significance cards."""

import argparse
from Logger import info, info_frame
from LimitConfig import load_config, output_paths, result_path


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--config", required=True, help="Configuration module or Python file")
  parser.add_argument("--method", choices=("AsymptoticLimits", "Significance"), default="AsymptoticLimits")
  parser.add_argument("--condor", action="store_true")
  args = parser.parse_args()

  info("Initializing ROOT...")
  import ROOT

  ROOT.gROOT.SetBatch(True)
  from LimitProducer import produce_limits, produce_significance

  config = load_config(args.config)
  paths = output_paths(config)
  if args.method == "Significance":
    values = produce_significance(config, condor=args.condor)
    for name, value in values.items():
      info(f"{name}: significance {value}")
    info_frame(f"Significance cards and logs were saved to:\n{paths.datacards}")
  else:
    produce_limits(config, condor=args.condor)
    info_frame(f"Limits were saved to:\n{result_path(config)}\nDatacards and Combine files:\n{paths.datacards}")


if __name__ == "__main__":
  main()
