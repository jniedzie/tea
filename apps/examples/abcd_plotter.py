#!/usr/bin/env python3
"""Run config-driven common-signal ABCD optimization and PDF diagnostics."""

from __future__ import annotations

import argparse
import importlib
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import ROOT
from ABCDPlotter import ABCDPlotter, DEFAULTS


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--config", required=True, help="Bare config module basename")
  for key in DEFAULTS:
    if key == "overlap_metric":
      parser.add_argument("--overlap_metric", choices=("cosine", "intersection"))
    else:
      parser.add_argument("--" + key, type=int if key == "min_signals" else float)
  args = parser.parse_args()
  ROOT.gROOT.SetBatch(True)
  if "/" in args.config or args.config.endswith(".py"):
    raise ValueError("Pass a bare config basename without .py")
  config = importlib.import_module(args.config)
  plotter = ABCDPlotter(config, args)
  result = plotter.calculate_best_points()
  result["provenance"]["config_sha256"] = hashlib.sha256(Path(config.__file__).read_bytes()).hexdigest()
  result["config"] = args.config
  output = Path(config.output_path)
  output.mkdir(parents=True, exist_ok=True)
  (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
  np.savez_compressed(
    output / "metric_maps.npz",
    **{f"{q}_{name}": values for q, fields in plotter.maps.items() for name, values in fields.items()},
  )
  plotter.render()
  print(f"ABCD {result['status']}: {result.get('reason', result.get('physical_boundaries'))}", flush=True)
  return 0


if __name__ == "__main__":
  try:
    sys.exit(main())
  except Exception as error:
    print(f"ABCD FAILED: {error}", file=sys.stderr, flush=True)
    sys.exit(1)
