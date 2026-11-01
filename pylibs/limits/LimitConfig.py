"""Shared configuration loading, input selection and limits output paths."""

from dataclasses import dataclass
import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def load_config(name: str) -> ModuleType:
  if name.endswith(".py") or "/" in name:
    path = Path(name).resolve()
    spec = importlib.util.spec_from_file_location("tea_limits_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
  return importlib.import_module(name)


@dataclass(frozen=True)
class OutputPaths:
  root: Path
  datacards: Path
  results: Path
  diagnostics: Path
  plots: Path


def output_paths(config: Any) -> OutputPaths:
  root = getattr(config, "limits_output_path", None)
  if root is None or not str(root).strip():
    raise ValueError("Set limits_output_path explicitly in the limits configuration")
  root = Path(root).expanduser().resolve()
  paths = OutputPaths(root, root / "datacards", root / "limit_results", root / "diagnostic_plots", root / "limit_plots")
  for directory in (paths.datacards, paths.results, paths.diagnostics, paths.plots):
    directory.mkdir(parents=True, exist_ok=True)
  return paths


def output_stem(config: Any) -> str:
  if hasattr(config, "histogram"):
    stem = "limits_" + config.histogram.getName()
    if getattr(config, "do_abcd", False):
      stem += "_ABCD" + ("pred" if config.use_abcd_prediction else "real")
    return stem
  if getattr(config, "limits_input", None) is not None:
    return Path(config.limits_input).stem
  return "limits"


def result_path(config: Any) -> Path:
  return output_paths(config).results / (output_stem(config) + ".json")


def plot_inputs(config: Any) -> list:
  from LimitPoint import read_points, validate_collection

  inline = getattr(config, "limit_points", None)
  path = getattr(config, "limits_input", None)
  if inline is not None and path is not None:
    raise ValueError("Specify either limit_points or limits_input, not both")
  if inline is not None:
    return validate_collection(inline)
  return read_points(path if path is not None else result_path(config))


def plot_paths(config: Any) -> list[Path]:
  formats = getattr(config, "output_formats", ("pdf",))
  return [output_paths(config).plots / f"{output_stem(config)}.{extension.lstrip('.')}" for extension in formats]
