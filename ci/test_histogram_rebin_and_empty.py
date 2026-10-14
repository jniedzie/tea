"""Display rebinning preserves weighted cells; empty input is not missing data."""

from array import array
from itertools import count
from math import sqrt
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

FRAMEWORK = Path(__file__).resolve().parents[1]
for directory in ("plotting", "logger"):
  sys.path.insert(0, str(FRAMEWORK / "pylibs" / directory))

try:
  import ROOT
except ImportError:
  ROOT = None
else:
  from Histogram import Histogram
  from HistogramNormalizer import HistogramNormalizer, NormalizationType
  from HistogramPlotter import HistogramPlotter
  from Legend import Legend
  from Sample import Sample, SampleType

  ROOT.gROOT.SetBatch(True)


@unittest.skipIf(ROOT is None, "PyROOT is required")
class HistogramRebinTest(unittest.TestCase):
  identifiers = count()

  def source(self, edges=(0.0, 1.0, 2.0, 4.0, 7.0, 8.0, 11.0)):
    source = ROOT.TH1D(f"rebin_source_{next(self.identifiers)}", "", len(edges) - 1, array("d", edges))
    source.SetDirectory(0)
    source.Sumw2()
    values = (1.0, -2.0, 3.0, 4.0, 5.0, 6.0)[: len(edges) - 1]
    for index, value in enumerate(values, 1):
      source.SetBinContent(index, value)
      source.SetBinError(index, index)
    source.SetBinContent(0, 1.5)
    source.SetBinError(0, 0.3)
    source.SetBinContent(source.GetNbinsX() + 1, -0.5)
    source.SetBinError(source.GetNbinsX() + 1, 0.2)
    return source

  def prepare(self, source, **kwargs):
    histogram = Histogram("weighted", **kwargs)
    histogram.set_hist(source)
    histogram.setup(Sample(name="signal", type=SampleType.signal))
    return histogram

  @staticmethod
  def edges(source):
    return tuple(source.GetBinLowEdge(index) for index in range(1, source.GetNbinsX() + 2))

  def test_rebin_merges_display_bins_and_keeps_short_final_group_and_flow_errors(self):
    source = self.source()
    before = source.Integral(0, source.GetNbinsX() + 1)
    histogram = self.prepare(source, bin_edges=(0.0, 2.0, 4.0, 8.0, 11.0), rebin=3)
    self.assertEqual(self.edges(histogram.hist), (0.0, 8.0, 11.0))
    self.assertEqual(histogram.hist.GetBinContent(1), 11.0)
    self.assertEqual(histogram.hist.GetBinContent(2), 6.0)
    self.assertAlmostEqual(histogram.hist.GetBinError(1), sqrt(55.0))
    self.assertAlmostEqual(histogram.hist.GetBinError(2), 6.0)
    self.assertEqual(histogram.hist.Integral(0, 3), before)
    self.assertEqual(histogram.hist.GetBinContent(0), 1.5)
    self.assertEqual(histogram.hist.GetBinContent(3), -0.5)
    self.assertAlmostEqual(histogram.hist.GetBinError(0), 0.3)
    self.assertAlmostEqual(histogram.hist.GetBinError(3), 0.2)

  def test_native_variable_axis_uses_rebin_factor_and_retains_remainder(self):
    source = self.source((0.0, 1.0, 2.0, 4.0, 7.0, 8.0))
    histogram = self.prepare(source, rebin=2)
    self.assertEqual(self.edges(histogram.hist), (0.0, 2.0, 7.0, 8.0))
    self.assertEqual([histogram.hist.GetBinContent(index) for index in range(1, 4)], [-1.0, 7.0, 5.0])
    self.assertEqual(histogram.hist.Integral(), 11.0)
    self.assertAlmostEqual(histogram.hist.GetBinError(2), 5.0)

  def test_width_normalization_is_applied_after_merged_bins(self):
    histogram = self.prepare(self.source(), bin_edges=(0.0, 2.0, 4.0, 8.0, 11.0), rebin=3, scale_by_bin_width=True)
    self.assertAlmostEqual(histogram.hist.GetBinContent(1), 11.0 / 8.0)
    self.assertAlmostEqual(histogram.hist.GetBinContent(2), 6.0 / 3.0)
    self.assertAlmostEqual(histogram.hist.GetBinError(1), sqrt(55.0) / 8.0)
    self.assertAlmostEqual(histogram.hist.GetBinError(2), 6.0 / 3.0)
    self.assertAlmostEqual(histogram.hist.Integral("width"), 17.0)

  def test_callable_edges_and_roundoff_use_recorded_source_edges(self):
    histogram = self.prepare(self.source(), bin_edges=lambda source: (0.0, 2.0 + 1.0e-11, 4.0, 8.0, 11.0), rebin=2)
    self.assertEqual(self.edges(histogram.hist), (0.0, 4.0, 11.0))
    self.assertEqual(histogram.hist.Integral(), 17.0)

  def test_exact_fine_edges_do_not_collapse_under_alignment_tolerance(self):
    histogram = self.prepare(self.source((0.0, 1.0e-12, 2.0e-12, 3.0e-12)), rebin=2)
    self.assertEqual(self.edges(histogram.hist), (0.0, 2.0e-12, 3.0e-12))
    self.assertEqual(histogram.hist.Integral(), 2.0)

  def test_invalid_factor_split_bins_and_collapsed_edges_are_rejected(self):
    for factor in (0, -1, 1.5, True):
      with self.subTest(factor=factor), self.assertRaises(ValueError):
        self.prepare(self.source(), rebin=factor)
    for edges in ((0.0, 2.5, 11.0), (0.0, 2.0, 2.0 + 1.0e-12, 11.0), (0.0, 2.0, 8.0)):
      with self.subTest(edges=edges), self.assertRaises(ValueError):
        self.prepare(self.source(), bin_edges=edges)
    for edges in ((1.0e-12, 3.0e-12), (0.0, 2.0e-12)):
      with self.subTest(edges=edges), self.assertRaises(ValueError):
        self.prepare(self.source((0.0, 1.0e-12, 2.0e-12, 3.0e-12)), bin_edges=edges)

  def test_density_shape_normalization_keeps_correct_area_after_rebin(self):
    histogram = self.prepare(
      self.source(),
      bin_edges=(0.0, 2.0, 4.0, 8.0, 11.0),
      rebin=3,
      scale_by_bin_width=True,
      norm_type=NormalizationType.to_background,
    )
    normalizer = HistogramNormalizer(SimpleNamespace(histograms=[histogram], samples=[]))
    normalizer.normalize(histogram, Sample(name="signal", type=SampleType.signal), total_backgrounds_integral=42.0)
    self.assertAlmostEqual(histogram.hist.Integral("width"), 42.0)
    self.assertAlmostEqual(histogram.hist.GetBinError(1), sqrt(55.0) / 8.0 * 42.0 / 17.0)


@unittest.skipIf(ROOT is None, "PyROOT is required")
class LegendHeaderTest(unittest.TestCase):
  def plotter(self, samples, legends):
    directory = tempfile.TemporaryDirectory()
    self.addCleanup(directory.cleanup)
    histogram = Histogram("category", legend_label="Both-Both")
    config = SimpleNamespace(
      histograms=[histogram], samples=[], legends=legends, output_path=directory.name, show_ratio_plots=False
    )
    plotter = HistogramPlotter(config)
    plotter.histosamples = [(histogram, sample) for sample in samples]
    return plotter, histogram

  def test_category_appears_once_in_highest_legend_regardless_of_sample_order(self):
    samples = [Sample(name="sm", type=SampleType.background), Sample(name="bsm", type=SampleType.signal)]
    legends = {SampleType.background: Legend(y2=0.5, title="SM"), SampleType.signal: Legend(y2=0.9, title="BSM")}
    for order in (samples, list(reversed(samples))):
      with self.subTest(order=[sample.name for sample in order]):
        plotter, histogram = self.plotter(order, legends)
        plotter.setupLegends()
        headers = {key: legend.GetHeader() for key, legend in plotter.legends[histogram.name].items()}
        self.assertEqual(headers[SampleType.background], "SM")
        self.assertEqual(headers[SampleType.signal], "BSM (Both-Both)")

  def test_custom_legend_title_is_preserved(self):
    samples = [
      Sample(name="special", type=SampleType.signal, custom_legend=Legend(y2=0.95, title="Special signal")),
      Sample(name="sm", type=SampleType.background),
    ]
    plotter, histogram = self.plotter(samples, {SampleType.background: Legend(y2=0.8, title="SM")})
    plotter.setupLegends()
    self.assertEqual(plotter.legends[histogram.name]["special"].GetHeader(), "Special signal (Both-Both)")
    self.assertEqual(plotter.legends[histogram.name][SampleType.background].GetHeader(), "SM")

  def test_single_visible_legend_keeps_category(self):
    samples = [Sample(name="sm", type=SampleType.background), Sample(name="bsm", type=SampleType.signal)]
    plotter, histogram = self.plotter(samples, {SampleType.background: Legend(title="SM"), SampleType.signal: None})
    plotter.setupLegends()
    self.assertEqual(plotter.legends[histogram.name][SampleType.background].GetHeader(), "SM (Both-Both)")
    self.assertIsNone(plotter.legends[histogram.name][SampleType.signal])

  def test_ratio_legends_show_category_once(self):
    samples = [Sample(name="sm", type=SampleType.background), Sample(name="bsm", type=SampleType.signal)]
    plotter, histogram = self.plotter(
      samples, {SampleType.background: Legend(y2=0.9, title="SM"), SampleType.signal: Legend(y2=0.5, title="BSM")}
    )
    plotter.histosamples = []
    passed = Histogram("selected_pass", legend_label=histogram.legend_label)
    total = Histogram("selected_total")
    plotter.ratiosamples = [(passed, total, sample) for sample in samples]
    plotter.setupLegends()
    self.assertEqual(plotter.legends["selected_ratio"][SampleType.background].GetHeader(), "SM (Both-Both)")
    self.assertEqual(plotter.legends["selected_ratio"][SampleType.signal].GetHeader(), "BSM")


@unittest.skipIf(ROOT is None, "PyROOT is required")
class EmptyHistogramPlotTest(unittest.TestCase):
  def test_duplicate_samples_are_skipped_but_failed_loads_can_be_retried(self):
    with tempfile.TemporaryDirectory() as temporary:
      histogram = Histogram("present", norm_type=NormalizationType.none)
      retry = Histogram("later", norm_type=NormalizationType.none)
      samples = [Sample(name="one"), Sample(name="two")]
      config = SimpleNamespace(
        histograms=[histogram, retry], samples=samples, output_path=temporary, show_ratio_plots=False
      )
      plotter = HistogramPlotter(config)
      source = ROOT.TH1D("duplicate_plot_source", "", 4, 0, 4)
      source.SetDirectory(0)
      source.Fill(1.5, 3.0)
      input_file = SimpleNamespace(Get=lambda name: source)
      plotter.addHistosample(histogram, samples[0], input_file)
      plotter.addHistosample(histogram, Sample(name="one"), input_file)
      plotter.addHistosample(histogram, samples[1], input_file)
      self.assertEqual(len(plotter.histosamples), 2)
      missing_file = SimpleNamespace(Get=lambda name: None, GetName=lambda: "partial.root")
      with patch("Histogram.warn"):
        plotter.addHistosample(retry, samples[0], missing_file)
      plotter.addHistosample(retry, samples[0], input_file)
      self.assertEqual(len(plotter.histosamples), 3)
      # Loading another sample must retain independent mutable ROOT contents.
      plotter.histosamples[0][0].hist.Scale(2.0)
      self.assertEqual(plotter.histosamples[1][0].hist.Integral(), 3.0)

  def test_empty_input_needs_no_legend_or_empty_pdf_and_emits_no_missing_warning(self):
    with tempfile.TemporaryDirectory() as temporary:
      histogram = Histogram("empty", norm_type=NormalizationType.none)
      samples = [Sample(name="one"), Sample(name="two")]
      config = SimpleNamespace(
        histograms=[histogram],
        samples=samples,
        output_path=temporary,
        show_ratio_plots=False,
        canvas_size=(400, 300),
        legends={SampleType.background: Legend()},
      )
      plotter = HistogramPlotter(config)
      source = ROOT.TH1D("empty_plot_source", "", 4, 0, 4)
      source.SetDirectory(0)
      input_file = SimpleNamespace(Get=lambda name: source, GetName=lambda: "present.root")
      with patch("Histogram.warn") as load_warning, patch("HistogramPlotter.warn") as plot_warning:
        for sample in samples:
          plotter.addHistosample(histogram, sample, input_file)
        plotter.setupLegends()
        plotter.buildStacks()
        plotter.drawStacks()
        load_warning.assert_not_called()
        plot_warning.assert_called_once_with("Skipping plot empty: no selected sample has drawable entries.")
      self.assertEqual(plotter.histosamples, [])
      self.assertEqual(source.GetEntries(), 0)
      self.assertEqual(source.Integral(), 0)
      self.assertEqual(list(Path(temporary).rglob("*.pdf")), [])

  def test_absent_object_reports_histogram_and_file_once(self):
    histogram = Histogram("missing", norm_type=NormalizationType.none)
    input_file = SimpleNamespace(Get=lambda name: None, GetName=lambda: "input.root")
    with patch("Histogram.warn") as warning:
      histogram.load(input_file)
      self.assertFalse(histogram.isGood())
      warning.assert_called_once()
      self.assertIn("missing", warning.call_args.args[0])
      self.assertIn("input.root", warning.call_args.args[0])


if __name__ == "__main__":
  unittest.main()
