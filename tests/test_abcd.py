from __future__ import annotations

import math
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

ROOT = pytest.importorskip("ROOT")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pylibs/abcdTools"))
from ABCDHelper import ABCDHelper
from ABCDSearch import metrics, regions, search

SETTINGS = dict(
  max_closure=0.2,
  max_error=2.0,
  min_n_events=20.0,
  max_signal_contamination=0.2,
  max_correlation=None,
  max_overlap=None,
  min_signals=1,
)


def plane(values: list[list[float]]) -> object:
  hist = ROOT.TH2D(uuid4().hex, "", len(values), 0.0, len(values), len(values[0]), 0.0, len(values[0]))
  hist.SetDirectory(0)
  hist.Sumw2()
  for i, row in enumerate(values, 1):
    for j, value in enumerate(row, 1):
      hist.SetBinContent(i, j, value)
      hist.SetBinError(i, j, 2 * math.sqrt(abs(value)))
  return hist


def test_all_required_models_pass_before_summed_ranking() -> None:
  background = plane([[100.0, 100.0], [10000.0, 10000.0], [100.0, 100.0]])
  signals = {"one": plane([[1.0, 1000.0], [1.0, 0.0], [1.0, 1.0]]), "two": plane([[1.0, 5.0], [1.0, 85.0], [1.0, 5.0]])}
  result, maps = search(background, signals, list(signals), SETTINGS, quadrant_order=("A",))
  assert result["indices"] == (3, 2)
  assert maps["A"]["significance"][0, 0] > maps["A"]["significance"][1, 0]
  assert maps["A"]["accepted"][0, 0] == 0
  assert result["metrics"]["significance"] == sum(result["individual_significances"].values())
  replay, _ = search(background, signals, list(signals), SETTINGS, result["physical_boundaries"], ("A",))
  assert replay["per_signal_metrics"] == result["per_signal_metrics"]


def test_helper_maps_share_integration_boundaries_and_weighted_errors() -> None:
  background, signal = plane([[100.0, 100.0], [100.0, 100.0]]), plane([[10.0, 70.0], [10.0, 10.0]])
  helper = ABCDHelper(SimpleNamespace(), SimpleNamespace(**SETTINGS))
  expected = metrics(helper, regions(helper, background, (2, 2), "A"), regions(helper, signal, (2, 2), "A"))
  assert helper.get_significance_hist(signal, background).GetBinContent(2, 2) == expected["significance"]
  assert helper.get_signal_contramination_hist(signal).GetBinContent(2, 2) == expected["leakage"]
  assert helper.get_optimization_hists(background)["error"].GetBinContent(2, 2) == pytest.approx(expected["error"])
