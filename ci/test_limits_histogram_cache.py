#!/usr/bin/env python3
"""Keep cached ROOT inputs unchanged when preparing limits for several signals."""

from pathlib import Path
import math
import sys
import tempfile
from types import SimpleNamespace
import unittest

import ROOT


REPO_ROOT = Path(__file__).resolve().parents[1]
for directory in ("logger", "plotting", "limits", "abcdTools"):
  sys.path.insert(0, str(REPO_ROOT / "pylibs" / directory))

from Histogram import Histogram, Histogram2D, Profile2D
from HistogramNormalizer import NormalizationType
from HistogramsManager import HistogramsManager
from Sample import Sample, SampleType


ROOT.gROOT.SetBatch(True)


class LimitsHistogramCacheTest(unittest.TestCase):
  def setUp(self):
    self.temporary_directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.temporary_directory.cleanup)
    self.directory = Path(self.temporary_directory.name)
    self.samples = (
      Sample(name="signal_a", type=SampleType.signal),
      Sample(name="signal_b", type=SampleType.signal),
      Sample(name="background", type=SampleType.background),
      Sample(name="data", type=SampleType.data),
    )

  def open_inputs(self, empty=False, kind="TH1D"):
    input_files = {}
    for sample in self.samples:
      sample.file_path = str(self.directory / f"{kind}_{sample.name}.root")
      with ROOT.TFile.Open(sample.file_path, "RECREATE"):
        if kind == "TH1D":
          histogram = ROOT.TH1D("observable", "", 8, 0.0, 8.0)
          histogram.Sumw2()
          if not empty:
            for index in range(1, 9):
              histogram.Fill(index - 0.5, index)
            histogram.Fill(-0.5, 2.0)
            histogram.Fill(8.5, 3.0)
        else:
          histogram = getattr(ROOT, kind)("observable", "", 4, 0.0, 4.0, 4, 0.0, 4.0)
          for x in (0.5, 1.5, 2.5, 3.5):
            for y in (0.5, 1.5, 2.5, 3.5):
              if kind == "TProfile2D":
                histogram.Fill(x, y, 2.0)
                histogram.Fill(x, y, 6.0)
              else:
                histogram.Fill(x, y)
        histogram.Write()
      input_files[sample.name] = ROOT.TFile.Open(sample.file_path, "READ")
      self.addCleanup(input_files[sample.name].Close)
    return input_files

  def managers_for_two_signals(self, histogram, input_files):
    config = SimpleNamespace(
      histogram=histogram,
      samples=self.samples,
      datacards_output_path=str(self.directory / "datacards"),
      plots_output_path=str(self.directory / "plots"),
    )
    managers = []
    for signal in self.samples[:2]:
      manager = HistogramsManager(config, input_files, f"datacard_{signal.name}")
      for sample in (signal, *self.samples[2:]):
        manager.addHistosample(histogram, sample)
      manager.normalizeHistograms()
      manager.buildStacks()
      managers.append({sample.name: hist for hist, sample in manager.histosamples})
    return managers

  def test_shared_background_and_data_are_rebinned_once_per_signal(self):
    input_files = self.open_inputs()
    histogram = Histogram(name="observable", rebin=2, norm_type=NormalizationType.none)
    managers = self.managers_for_two_signals(histogram, input_files)

    for sample in self.samples[2:]:
      prepared = [manager[sample.name].hist for manager in managers]
      self.assertEqual([hist.GetNbinsX() for hist in prepared], [4, 4])
      for hist in prepared:
        self.assertEqual([hist.GetBinContent(index) for index in range(6)], [2.0, 3.0, 7.0, 11.0, 15.0, 3.0])
        for index, variance in enumerate((4.0, 5.0, 25.0, 61.0, 113.0, 9.0)):
          self.assertAlmostEqual(hist.GetSumw2()[index], variance)
          self.assertAlmostEqual(hist.GetBinError(index), math.sqrt(variance))
        self.assertEqual(hist.GetEntries(), 10.0)
        self.assertEqual(hist.GetBinErrorOption(), ROOT.TH1.kPoisson)
        self.assertFalse(hist.GetDirectory())
      prepared[0].Scale(2.0)
      self.assertEqual(prepared[1].GetBinContent(1), 3.0)

      source = input_files[sample.name].Get("observable")
      self.assertEqual(source.GetNbinsX(), 8)
      self.assertEqual([source.GetBinContent(index) for index in range(10)], [2.0, *map(float, range(1, 9)), 3.0])
      self.assertEqual(list(source.GetSumw2()), [4.0, *[float(index * index) for index in range(1, 9)], 9.0])
      self.assertEqual(source.GetBinErrorOption(), ROOT.TH1.kNormal)

  def test_empty_histogram_placeholder_does_not_change_cached_input(self):
    input_files = self.open_inputs(empty=True)
    histogram = Histogram(name="observable", rebin=2, norm_type=NormalizationType.none)
    managers = self.managers_for_two_signals(histogram, input_files)

    for sample in self.samples[2:]:
      for manager in managers:
        prepared = manager[sample.name]
        self.assertEqual(prepared.entries, 0)
        self.assertEqual(prepared.hist.GetEntries(), 1.0)
        self.assertEqual(prepared.hist.GetNbinsX(), 4)
        self.assertEqual(prepared.hist.Integral(), 1e-99)
      source = input_files[sample.name].Get("observable")
      self.assertEqual(source.GetEntries(), 0.0)
      self.assertEqual(source.GetNbinsX(), 8)
      self.assertEqual(source.Integral(), 0.0)

  def test_loaded_histogram_survives_closing_its_input(self):
    input_files = self.open_inputs()
    histograms = (
      Histogram(name="observable", norm_type=NormalizationType.none),
      Histogram(name="observable", norm_type=NormalizationType.none, x_min=2.0, x_max=6.0),
    )
    for histogram in histograms:
      histogram.load(input_files["background"])
      self.assertFalse(histogram.hist.GetDirectory())
    input_files["background"].Close()
    self.assertEqual(histograms[0].hist.GetNbinsX(), 8)
    self.assertEqual(histograms[0].hist.Integral(), 36.0)
    self.assertEqual(histograms[1].hist.GetNbinsX(), 4)
    self.assertEqual(histograms[1].hist.Integral(), 18.0)

  def test_missing_histogram_still_returns_without_cloning(self):
    input_files = self.open_inputs()
    histogram = Histogram(name="missing", norm_type=NormalizationType.none)
    histogram.load(input_files["background"])
    self.assertFalse(histogram.isGood())

  def test_two_dimensional_histograms_and_profile_means_remain_independent(self):
    for kind, wrapper in (("TH2D", Histogram2D), ("TProfile2D", Profile2D)):
      with self.subTest(kind=kind):
        input_files = self.open_inputs(kind=kind)
        options = {"norm_type": NormalizationType.none} if wrapper is Histogram2D else {}
        histogram = wrapper(name="observable", x_rebin=2, y_rebin=2, **options)
        managers = self.managers_for_two_signals(histogram, input_files)
        for sample in self.samples[2:]:
          for manager in managers:
            prepared = manager[sample.name].hist
            self.assertEqual((prepared.GetNbinsX(), prepared.GetNbinsY()), (2, 2))
            self.assertEqual(prepared.GetBinContent(1, 1), 4.0)
            self.assertEqual(prepared.ClassName(), kind)
            expected_error = math.sqrt(0.5) if kind == "TProfile2D" else 2.0
            self.assertAlmostEqual(prepared.GetBinError(1, 1), expected_error)
          source = input_files[sample.name].Get("observable")
          self.assertEqual((source.GetNbinsX(), source.GetNbinsY()), (4, 4))


if __name__ == "__main__":
  unittest.main()
