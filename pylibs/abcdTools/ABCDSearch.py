"""Weighted, analysis-independent ABCD regions and common-signal cut search."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from ABCDHelper import ABCDHelper

PERMUTATIONS = {"A": (0, 1, 2, 3), "B": (1, 0, 3, 2), "C": (2, 3, 0, 1), "D": (3, 2, 1, 0)}
DIRECTIONS = {"A": ("<", ">="), "B": ("<", "<"), "C": (">=", ">="), "D": (">=", "<")}
BOUNDARY_CONVENTION = (
  "Indices name the first high-side bin; low uses < boundary, high uses >= boundary; flow bins excluded."
)


class IntegralPlane:
  """Prefix integrals expose TEA's TH2 integration API without repeated bin walks."""

  def __init__(self, hist: Any) -> None:
    self.nx, self.ny = hist.GetNbinsX(), hist.GetNbinsY()
    values = np.array([[hist.GetBinContent(i, j) for j in range(1, self.ny + 1)] for i in range(1, self.nx + 1)])
    variances = np.array([[hist.GetBinError(i, j) ** 2 for j in range(1, self.ny + 1)] for i in range(1, self.nx + 1)])
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(variances)):
      raise ValueError("Nonfinite ABCD bin contents or stored errors")
    self.sums = np.pad(values.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    self.squares = np.pad(variances.cumsum(0).cumsum(1), ((1, 0), (1, 0)))

  def GetNbinsX(self) -> int:
    return self.nx

  def GetNbinsY(self) -> int:
    return self.ny

  def IntegralAndError(self, x1: int, x2: int, y1: int, y2: int, error: Any) -> float:
    if x2 < x1 or y2 < y1:
      error.value = 0.0
      return 0.0

    def rectangle(prefix: np.ndarray) -> float:
      return float(prefix[x2, y2] - prefix[x1 - 1, y2] - prefix[x2, y1 - 1] + prefix[x1 - 1, y1 - 1])

    error.value = math.sqrt(max(0.0, rectangle(self.squares)))
    return rectangle(self.sums)


def regions(helper: ABCDHelper, plane: Any, point: tuple[int, int], quadrant: str) -> tuple[list[float], list[float]]:
  values = helper.get_abcd(plane, point, raw_errors=False)
  order = PERMUTATIONS[quadrant]
  return [values[i] for i in order], [values[i + 4] for i in order]


def region_table(yields: list[float], errors: list[float]) -> dict:
  return {
    name: {"yield": value, "error": error, "effective_entries": value**2 / error**2 if error > 0 else None}
    for name, value, error in zip("ABCD", yields, errors)
  }


def metrics(
  helper: ABCDHelper, background: tuple[list[float], list[float]], signal: tuple[list[float], list[float]]
) -> dict | None:
  b, be = background
  s, se = signal
  if any(v <= 0 or not math.isfinite(v) for v in b) or sum(s) <= 0 or s[0] <= 0:
    return None
  prediction, prediction_error = helper.get_prediction(*b[1:], *be[1:])
  combined = math.hypot(be[0], prediction_error)
  if combined <= 0:
    return None
  result = {
    "significance": s[0] / math.sqrt(s[0] + b[0]),
    "closure": abs(b[0] - prediction) / b[0],
    "error": abs(b[0] - prediction) / combined,
    "min_n_events": min(b),
    "leakage": max(s[1:]) / sum(s),
    "control_leakage": {name: value / sum(s) for name, value in zip("BCD", s[1:])},
    "prediction": prediction,
    "prediction_error": prediction_error,
    "background": region_table(b, be),
    "signal": region_table(s, se),
  }
  return result if all(math.isfinite(result[k]) for k in ("significance", "closure", "error", "leakage")) else None


def accepted(values: dict, settings: dict) -> bool:
  return (
    values["closure"] <= settings["max_closure"]
    and values["error"] <= settings["max_error"]
    and values["min_n_events"] >= settings["min_n_events"]
    and values["leakage"] <= settings["max_signal_contamination"]
  )


def effective_entries(hist: Any, flow: bool) -> float | None:
  from ctypes import c_double

  error = c_double()
  nx, ny = hist.GetNbinsX(), hist.GetNbinsY()
  value = hist.IntegralAndError(
    0 if flow else 1, nx + 1 if flow else nx, 0 if flow else 1, ny + 1 if flow else ny, error
  )
  return value**2 / error.value**2 if error.value else None


def overlap(hist: Any, background: Any, metric: str = "intersection") -> float | None:
  s, b = hist.Integral(), background.Integral()
  if s <= 0 or b <= 0:
    return None
  values = [
    (hist.GetBinContent(i, j) / s, background.GetBinContent(i, j) / b)
    for i in range(1, hist.GetNbinsX() + 1)
    for j in range(1, hist.GetNbinsY() + 1)
  ]
  # Signed distributions have no probability-overlap interpretation.
  if any(min(pair) < 0 for pair in values):
    return None
  if metric == "intersection":
    return sum(min(pair) for pair in values)
  if metric == "cosine":
    numerator = sum(a * b for a, b in values)
    denominator = math.sqrt(sum(a * a for a, _ in values) * sum(b * b for _, b in values))
    return numerator / denominator if denominator else None
  raise ValueError(f"Unknown overlap metric: {metric}")


def boundary_indices(hist: Any, point: dict) -> tuple[int, int]:
  indices = []
  for axis, name in ((hist.GetXaxis(), "x"), (hist.GetYaxis(), "y")):
    matches = [
      i
      for i in range(2, axis.GetNbins() + 1)
      if math.isclose(axis.GetBinLowEdge(i), point[name], rel_tol=0.0, abs_tol=1e-10)
    ]
    if len(matches) != 1:
      raise ValueError(f"Frozen {name} boundary does not coincide with an interior rebinned edge")
    indices.append(matches[0])
  return tuple(indices)


def search(
  background: Any,
  signals: dict[str, Any],
  selected: list[str],
  settings: dict,
  fixed_point: dict | None = None,
  quadrant_order: tuple[str, ...] = ("A", "B", "C", "D"),
) -> tuple[dict, dict]:
  if not selected or len(set(selected)) != len(selected):
    raise ValueError("Select a nonempty, unique optimization signal set")
  if (
    not quadrant_order
    or len(set(quadrant_order)) != len(quadrant_order)
    or any(q not in DIRECTIONS for q in quadrant_order)
  ):
    raise ValueError("Select unique quadrants from A, B, C, D")
  if any(key not in signals for key in selected):
    raise ValueError("Missing selected signal histogram")
  helper = ABCDHelper()
  correlation = float(background.GetCorrelationFactor())
  coefficient = settings.get("overlap_metric", "intersection")
  overlaps = {key: overlap(hist, background, coefficient) for key, hist in signals.items()}
  result = {
    "optimization_signals": selected,
    "objective": "sum_individual_significances",
    "correlation": correlation if math.isfinite(correlation) else None,
    "overlap": overlaps,
    "overlap_metric": coefficient,
  }
  names = ("significance", "closure", "error", "leakage", "min_n_events", "accepted")
  shape = (background.GetNbinsX() - 1, background.GetNbinsY() - 1)
  maps = {q: {name: np.full(shape, np.nan) for name in names} for q in quadrant_order}
  for key in signals:
    for fields in maps.values():
      for name in ("significance", "leakage"):
        fields[f"{name}:{key}"] = np.full(shape, np.nan)
  empty = [key for key in selected if not math.isfinite(signals[key].Integral()) or signals[key].Integral() <= 0]
  if empty:
    return {
      **result,
      "status": "unavailable",
      "reason": f"Required signals have nonpositive in-range yield: {empty}",
    }, maps
  limit = settings.get("max_correlation")
  if limit is not None and (result["correlation"] is None or abs(correlation) > limit):
    return {**result, "status": "rejected", "reason": "Correlation constraint"}, maps
  limit = settings.get("max_overlap")
  if limit is not None and any(overlaps[key] is None or overlaps[key] > limit for key in selected):
    return {**result, "status": "rejected", "reason": "Required signal overlap constraint"}, maps
  if len(selected) < settings.get("min_signals", 0):
    return {**result, "status": "rejected", "reason": "Too few selected signals"}, maps
  bp = IntegralPlane(background)
  sp = {key: IntegralPlane(hist) for key, hist in signals.items()}
  points = (
    [boundary_indices(background, fixed_point)]
    if fixed_point
    else [(i, j) for i in range(2, background.GetNbinsX() + 1) for j in range(2, background.GetNbinsY() + 1)]
  )
  best = None
  for q in quadrant_order:
    print(f"Scanning quadrant {q}: {len(points)} boundaries, {len(selected)} required signals", flush=True)
    for number, point in enumerate(points, 1):
      if number % 10000 == 0:
        print(f"Quadrant {q}: evaluated {number} boundaries", flush=True)
      b = regions(helper, bp, point, q)
      if any(v <= 0 or not math.isfinite(v) for v in b[0]):
        continue
      evaluations = {}
      for key in selected:
        values = metrics(helper, b, regions(helper, sp[key], point, q))
        if values is not None:
          evaluations[key] = values
          for name in ("significance", "leakage"):
            maps[q][f"{name}:{key}"][point[0] - 2, point[1] - 2] = values[name]
      if len(evaluations) != len(selected):
        continue
      first = evaluations[selected[0]]
      values = {
        **first,
        "significance": sum(v["significance"] for v in evaluations.values()),
        "leakage": max(v["leakage"] for v in evaluations.values()),
      }
      if len(selected) > 1:
        values.pop("signal")
        values.pop("control_leakage")
      valid = all(accepted(v, settings) for v in evaluations.values())
      for name in names:
        maps[q][name][point[0] - 2, point[1] - 2] = float(valid) if name == "accepted" else values[name]
      if valid and (best is None or values["significance"] > best["metrics"]["significance"]):
        best = {
          "quadrant": q,
          "indices": point,
          "metrics": values,
          "per_signal_metrics": evaluations,
          "aggregate_score": values["significance"],
          "individual_significances": {key: v["significance"] for key, v in evaluations.items()},
        }
  if best is None:
    return {**result, "status": "rejected", "reason": "No boundary satisfies every required signal"}, maps
  i, j = best["indices"]
  return {
    **result,
    "status": "accepted",
    **best,
    "physical_boundaries": {"x": background.GetXaxis().GetBinLowEdge(i), "y": background.GetYaxis().GetBinLowEdge(j)},
    "directions": dict(zip(("x", "y"), DIRECTIONS[best["quadrant"]])),
    "boundary_convention": BOUNDARY_CONVENTION,
  }, maps
