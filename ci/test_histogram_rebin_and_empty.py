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
for directory in ('plotting', 'logger'):
  sys.path.insert(0, str(FRAMEWORK / 'pylibs' / directory))

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


@unittest.skipIf(ROOT is None, 'PyROOT is required')
class HistogramRebinTest(unittest.TestCase):
  identifiers = count()

  def source(self, edges=(0., 1., 2., 4., 7., 8., 11.)):
    source = ROOT.TH1D(f'rebin_source_{next(self.identifiers)}', '', len(edges) - 1, array('d', edges))
    source.SetDirectory(0)
    source.Sumw2()
    values = (1., -2., 3., 4., 5., 6.)[:len(edges) - 1]
    for index, value in enumerate(values, 1):
      source.SetBinContent(index, value)
      source.SetBinError(index, index)
    source.SetBinContent(0, 1.5)
    source.SetBinError(0, .3)
    source.SetBinContent(source.GetNbinsX() + 1, -.5)
    source.SetBinError(source.GetNbinsX() + 1, .2)
    return source

  def prepare(self, source, **kwargs):
    histogram = Histogram('weighted', **kwargs)
    histogram.set_hist(source)
    histogram.setup(Sample(name='signal', type=SampleType.signal))
    return histogram

  @staticmethod
  def edges(source):
    return tuple(source.GetBinLowEdge(index) for index in range(1, source.GetNbinsX() + 2))

  def test_rebin_merges_display_bins_and_keeps_short_final_group_and_flow_errors(self):
    source = self.source()
    before = source.Integral(0, source.GetNbinsX() + 1)
    histogram = self.prepare(source, bin_edges=(0., 2., 4., 8., 11.), rebin=3)
    self.assertEqual(self.edges(histogram.hist), (0., 8., 11.))
    self.assertEqual(histogram.hist.GetBinContent(1), 11.)
    self.assertEqual(histogram.hist.GetBinContent(2), 6.)
    self.assertAlmostEqual(histogram.hist.GetBinError(1), sqrt(55.))
    self.assertAlmostEqual(histogram.hist.GetBinError(2), 6.)
    self.assertEqual(histogram.hist.Integral(0, 3), before)
    self.assertEqual(histogram.hist.GetBinContent(0), 1.5)
    self.assertEqual(histogram.hist.GetBinContent(3), -.5)
    self.assertAlmostEqual(histogram.hist.GetBinError(0), .3)
    self.assertAlmostEqual(histogram.hist.GetBinError(3), .2)

  def test_native_variable_axis_uses_rebin_factor_and_retains_remainder(self):
    source = self.source((0., 1., 2., 4., 7., 8.))
    histogram = self.prepare(source, rebin=2)
    self.assertEqual(self.edges(histogram.hist), (0., 2., 7., 8.))
    self.assertEqual([histogram.hist.GetBinContent(index) for index in range(1, 4)], [-1., 7., 5.])
    self.assertEqual(histogram.hist.Integral(), 11.)
    self.assertAlmostEqual(histogram.hist.GetBinError(2), 5.)

  def test_width_normalization_is_applied_after_merged_bins(self):
    histogram = self.prepare(self.source(), bin_edges=(0., 2., 4., 8., 11.),
                             rebin=3, scale_by_bin_width=True)
    self.assertAlmostEqual(histogram.hist.GetBinContent(1), 11. / 8.)
    self.assertAlmostEqual(histogram.hist.GetBinContent(2), 6. / 3.)
    self.assertAlmostEqual(histogram.hist.GetBinError(1), sqrt(55.) / 8.)
    self.assertAlmostEqual(histogram.hist.GetBinError(2), 6. / 3.)
    self.assertAlmostEqual(histogram.hist.Integral('width'), 17.)

  def test_callable_edges_and_roundoff_use_recorded_source_edges(self):
    histogram = self.prepare(self.source(), bin_edges=lambda source: (0., 2. + 1.e-11, 4., 8., 11.), rebin=2)
    self.assertEqual(self.edges(histogram.hist), (0., 4., 11.))
    self.assertEqual(histogram.hist.Integral(), 17.)

  def test_exact_fine_edges_do_not_collapse_under_alignment_tolerance(self):
    histogram = self.prepare(self.source((0., 1.e-12, 2.e-12, 3.e-12)), rebin=2)
    self.assertEqual(self.edges(histogram.hist), (0., 2.e-12, 3.e-12))
    self.assertEqual(histogram.hist.Integral(), 2.)

  def test_invalid_factor_split_bins_and_collapsed_edges_are_rejected(self):
    for factor in (0, -1, 1.5, True):
      with self.subTest(factor=factor), self.assertRaises(ValueError):
        self.prepare(self.source(), rebin=factor)
    for edges in ((0., 2.5, 11.), (0., 2., 2. + 1.e-12, 11.), (0., 2., 8.)):
      with self.subTest(edges=edges), self.assertRaises(ValueError):
        self.prepare(self.source(), bin_edges=edges)
    for edges in ((1.e-12, 3.e-12), (0., 2.e-12)):
      with self.subTest(edges=edges), self.assertRaises(ValueError):
        self.prepare(self.source((0., 1.e-12, 2.e-12, 3.e-12)), bin_edges=edges)

  def test_density_shape_normalization_keeps_correct_area_after_rebin(self):
    histogram = self.prepare(self.source(), bin_edges=(0., 2., 4., 8., 11.), rebin=3,
                             scale_by_bin_width=True, norm_type=NormalizationType.to_background)
    normalizer = HistogramNormalizer(SimpleNamespace(histograms=[histogram], samples=[]))
    normalizer.normalize(histogram, Sample(name='signal', type=SampleType.signal),
                         total_backgrounds_integral=42.)
    self.assertAlmostEqual(histogram.hist.Integral('width'), 42.)
    self.assertAlmostEqual(histogram.hist.GetBinError(1), sqrt(55.) / 8. * 42. / 17.)


@unittest.skipIf(ROOT is None, 'PyROOT is required')
class EmptyHistogramPlotTest(unittest.TestCase):
  def test_empty_input_needs_no_legend_or_empty_pdf_and_emits_no_missing_warning(self):
    with tempfile.TemporaryDirectory() as temporary:
      histogram = Histogram('empty', norm_type=NormalizationType.none)
      samples = [Sample(name='one'), Sample(name='two')]
      config = SimpleNamespace(histograms=[histogram], samples=samples, output_path=temporary,
          show_ratio_plots=False, canvas_size=(400, 300), legends={SampleType.background: Legend()})
      plotter = HistogramPlotter(config)
      source = ROOT.TH1D('empty_plot_source', '', 4, 0, 4)
      source.SetDirectory(0)
      input_file = SimpleNamespace(Get=lambda name: source, GetName=lambda: 'present.root')
      with patch('Histogram.warn') as load_warning, patch('HistogramPlotter.warn') as plot_warning:
        for sample in samples:
          plotter.addHistosample(histogram, sample, input_file)
        plotter.setupLegends()
        plotter.buildStacks()
        plotter.drawStacks()
        load_warning.assert_not_called()
        plot_warning.assert_not_called()
      self.assertEqual(plotter.histosamples, [])
      self.assertEqual(source.GetEntries(), 0)
      self.assertEqual(source.Integral(), 0)
      self.assertEqual(list(Path(temporary).rglob('*.pdf')), [])

  def test_absent_object_reports_histogram_and_file_once(self):
    histogram = Histogram('missing', norm_type=NormalizationType.none)
    input_file = SimpleNamespace(Get=lambda name: None, GetName=lambda: 'input.root')
    with patch('Histogram.warn') as warning:
      histogram.load(input_file)
      self.assertFalse(histogram.isGood())
      warning.assert_called_once()
      self.assertIn('missing', warning.call_args.args[0])
      self.assertIn('input.root', warning.call_args.args[0])


if __name__ == '__main__':
  unittest.main()
