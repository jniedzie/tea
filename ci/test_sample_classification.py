#!/usr/bin/env python3
"""Sample metadata determines datacard roles, including synthetic processes."""

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import ROOT

REPO = Path(__file__).resolve().parents[1]
for directory in ("limits", "plotting", "logger", "abcdTools"):
  sys.path.insert(0, str(REPO / "pylibs" / directory))

from DatacardsProcessor import DatacardsProcessor, NoSensitivityError  # noqa: E402
from Histogram import Histogram, Histogram2D  # noqa: E402
from HistogramNormalizer import NormalizationType  # noqa: E402
from HistogramsManager import HistogramsManager  # noqa: E402
from Sample import Sample, SampleType  # noqa: E402

ROOT.gROOT.SetBatch(True)


class SampleClassificationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.path = Path(self.temp.name)

  def fixture(self, abcd: bool = False) -> tuple:
    wrapper = Histogram2D if abcd else Histogram
    histogram = wrapper(name="observable", norm_type=NormalizationType.none)
    config = SimpleNamespace(
      histogram=histogram,
      limits_output_path=self.path,
      do_abcd=abcd,
      use_abcd_prediction=True,
      signal_bin="A",
      abcd_point=(2, 2),
      rebin_2D=1,
      include_shapes=True,
      nuisances={},
      samples=[],
    )
    return config, DatacardsProcessor(config, "card")

  def histosample(self, name: str, kind: SampleType, value: float, abcd: bool = False) -> tuple:
    if abcd:
      raw = ROOT.TH2D(name, "", 2, 0, 2, 2, 0, 2)
      for x in (1, 2):
        for y in (1, 2):
          raw.SetBinContent(x, y, value)
      hist = Histogram2D(name="observable", norm_type=NormalizationType.none)
    else:
      raw = ROOT.TH1D(name, "", 2, 0, 2)
      raw.SetBinContent(1, value)
      hist = Histogram(name="observable", norm_type=NormalizationType.none)
    raw.SetDirectory(0)
    hist.set_hist(raw)
    return hist, Sample(name=name, type=kind)

  def test_arbitrary_names_rates_process_order_and_nuisances(self) -> None:
    for abcd in (False, True):
      with self.subTest(abcd=abcd):
        config, processor = self.fixture(abcd)
        signal = self.histosample("charged_particle", SampleType.signal, 2, abcd)
        background = self.histosample("contains_signal", SampleType.background, 10, abcd)
        observation = self.histosample("measured", SampleType.data, 10, abcd)
        path = processor.create_new_datacard(
          "observable",
          observation,
          {"contains_signal": background},
          signal,
          {"model": {"charged_particle": 1.1}, "background_norm": {"contains_signal": 1.2}},
          {},
        )
        text = path.read_text()
        self.assertIn("process signal " + ("bkg" if abcd else "contains_signal"), text)
        self.assertIn("process 0 1", text)
        self.assertIn("rate 2.0 10.0", text)
        self.assertIn("model lnN 1.1 -", text)
        self.assertIn("background_norm lnN - 1.2", text)
        if abcd:
          self.assertEqual(processor.histosamples["bkg"][1].type, SampleType.background)
          self.assertTrue((self.path / "diagnostic_plots/card.pdf").exists())
        self.assertEqual(signal[1].type, SampleType.signal)

  def test_empty_backgrounds_get_background_dummy_and_data_observation(self) -> None:
    for abcd in (False, True):
      with self.subTest(abcd=abcd):
        config, processor = self.fixture(abcd)
        signal = self.histosample("charged_particle", SampleType.signal, 2, abcd)
        empty = self.histosample("signal_in_background_name", SampleType.background, 0, abcd)
        manager = HistogramsManager(config, {}, "card")
        observation = manager._HistogramsManager__get_backgrounds_sum_hist({"empty": empty})
        self.assertEqual(observation[1].type, SampleType.data)
        path = processor.create_new_datacard("observable", observation, {empty[1].name: empty}, signal, {}, {})
        self.assertNotIn(empty[1].name, processor.histosamples)
        self.assertEqual(processor.histosamples["background_dummy"][1].type, SampleType.background)
        self.assertEqual(processor._DatacardsProcessor__get_first_background_name(), "background_dummy")
        self.assertIs(processor._DatacardsProcessor__get_signal_hist(), signal[0].hist)
        self.assertIn("process 0 1", path.read_text())
        self.assertEqual(signal[1].type, SampleType.signal)

  def test_zero_signal_is_no_sensitivity(self) -> None:
    _, processor = self.fixture()
    signal = self.histosample("charged_particle", SampleType.signal, 0)
    observation = self.histosample("measured", SampleType.data, 10)
    with self.assertRaises(NoSensitivityError):
      processor.create_new_datacard("observable", observation, {}, signal, {}, {})


if __name__ == "__main__":
  unittest.main()
