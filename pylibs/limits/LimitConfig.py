"""Explicit configuration loading and presentation compatibility helpers."""

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any
from LimitPlotter import PlotOptions


def load_config(name: str) -> ModuleType:
  if name.endswith(".py") or "/" in name:
    path = Path(name).resolve()
    spec = importlib.util.spec_from_file_location("tea_limits_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
  return importlib.import_module(name)


def output_stem(config: Any) -> str:
  stem = "limits_" + config.histogram.getName()
  if getattr(config, "do_abcd", False):
    stem += "_ABCD" + ("pred" if config.use_abcd_prediction else "real")
  return stem


def plot_options(config: Any) -> PlotOptions:
  if hasattr(config, "plot_options"):
    return config.plot_options
  # Compatibility for old flat ALP presentation configs; names/coordinates still require an adapter.
  return PlotOptions(
    x_title=getattr(config, "x_title", "x"),
    y_title=getattr(config, "y_title", "95% CL upper limit on r"),
    x_range=(config.x_min, config.x_max) if hasattr(config, "x_min") else None,
    y_range=(config.y_min, config.y_max) if hasattr(config, "y_min") else None,
    log_x=getattr(config, "log_x", True),
    log_y=getattr(config, "log_y", True),
    luminosity=config.luminosity / 1000 if hasattr(config, "luminosity") else None,
    quantity="cross_section" if hasattr(config, "reference_cross_section") else "r",
    constant_scale=getattr(config, "reference_cross_section", None),
    show_observed=getattr(config, "show_observed", False),
  )
