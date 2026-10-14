#!/usr/bin/env python3
"""ROOT rendering regressions; run with a Python environment providing PyROOT."""

from array import array
from itertools import count
from math import hypot
from pathlib import Path
import sys
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

FRAMEWORK = Path(__file__).resolve().parents[1]
for directory in ("plotting", "logger"):
  sys.path.insert(0, str(FRAMEWORK / "pylibs" / directory))

try:
  import ROOT
except ImportError:
  ROOT = None
else:
  from Histogram import Histogram
  from HistogramNormalizer import NormalizationType
  from HistogramPlotter import HistogramPlotter
  from CmsLabelsManager import CmsLabel
  from Legend import Legend
  from Sample import Sample, SampleType
  from Styler import Styler
  ROOT.gROOT.SetBatch(True)


@unittest.skipIf(ROOT is None, "PyROOT is required for rendered-axis tests")
class PlotLayoutTest(unittest.TestCase):
  identifiers = count()

  def setUp(self):
    self.objects = []
    self.canvases = []
    self.styler = Styler(SimpleNamespace(auto_adjust_axes_for_legend=True))
    self.styler.configureAutomaticMargins(
      [(1, 1e13)], (800, 600), ["#chi^{2}", "generator mother"],
      x_tick_labels=["unmatched", "different mothers", "bottom hadron"],
    )

  def tearDown(self):
    for canvas in self.canvases:
      canvas.Close()

  def source(self, edges, values, labels=()):
    name = "layout_source_%d" % next(self.identifiers)
    source = ROOT.TH1D(name, "", len(edges) - 1, array("d", edges))
    source.SetDirectory(0)
    source.SetFillColor(ROOT.kBlue)
    for index, value in enumerate(values, 1):
      source.SetBinContent(index, value)
      source.SetBinError(index, 0.15 * value)
    for index, label in enumerate(labels, 1):
      source.GetXaxis().SetBinLabel(index, label)
    self.objects.append(source)
    return source

  def draw(self, source, spec, with_legend=False, legend_box=(0.68, 0.60, 0.93, 0.90)):
    name = "layout_canvas_%d" % next(self.identifiers)
    canvas = ROOT.TCanvas(name, "", 800, 600)
    self.canvases.append(canvas)
    self.styler.preparePlotLayout(spec, [source], canvas)
    canvas.Divide(1, 1)
    pad = canvas.cd(1)
    self.styler.setup_main_pad_without_ratio(pad, bool(self.styler.categoricalLabels([source])))
    pad.SetLogx(spec.log_x)
    pad.SetLogy(spec.log_y)
    stack = ROOT.THStack(name + "_stack", "")
    stack.Add(source)
    self.objects.append(stack)
    self.styler.prepareDisplayFrame(stack)
    stack.Draw("hist")
    self.styler.setupFigure(stack, spec, source_histograms=[source])
    # The uncertainty band must also be included in the visible footprint.
    source.Draw("same e2")
    legend = None
    if with_legend:
      legend = ROOT.TLegend(*legend_box)
      legend.SetTextFont(43)
      legend.SetTextSize(22)
      for index in range(6):
        legend.AddEntry(source, "Sample %d" % index, "f")
      legend.Draw()
      self.objects.append(legend)
    pad.Modified()
    pad.Update()
    if legend:
      self.styler.adjustAxesForLegend(stack, spec, [source], [legend], pad)
      pad.Modified()
      pad.Update()
    return canvas, pad, stack, legend

  def assert_legend_clear(self, pad, source, legend):
    """Compare actual rendered pixel coordinates, independently of the solver."""
    legend_left = pad.UtoAbsPixel(legend.GetX1NDC())
    legend_right = pad.UtoAbsPixel(legend.GetX2NDC())
    legend_bottom = pad.VtoAbsPixel(legend.GetY1NDC())
    x_min = 10 ** pad.GetUxmin() if pad.GetLogx() else pad.GetUxmin()
    x_max = 10 ** pad.GetUxmax() if pad.GetLogx() else pad.GetUxmax()
    for index in range(1, source.GetNbinsX() + 1):
      x1 = source.GetXaxis().GetBinLowEdge(index)
      x2 = source.GetXaxis().GetBinUpEdge(index)
      if x2 <= x_min or x1 >= x_max:
        continue
      left = pad.XtoAbsPixel(pad.XtoPad(x1))
      right = pad.XtoAbsPixel(pad.XtoPad(x2))
      if right < legend_left or left > legend_right:
        continue
      height = source.GetBinContent(index) + source.GetBinError(index)
      if height <= 0:
        continue
      top = pad.YtoAbsPixel(pad.YtoPad(height))
      self.assertGreater(top, legend_bottom, "bin %d overlaps the rendered legend" % index)

  def draw_plotter_stacks(self, spec, backgrounds, signals=(), signal_options="nostack hist",
                          show_signal_stat_uncertainty=False):
    directory = tempfile.TemporaryDirectory()
    self.addCleanup(directory.cleanup)
    config = SimpleNamespace(
      histograms=[spec], samples=[], output_path=directory.name, canvas_size=(800, 600),
      show_ratio_plots=False, auto_adjust_axes_for_legend=True,
      show_signal_stat_uncertainty=show_signal_stat_uncertainty,
      plot_margins={"left": .13, "right": .35, "top": .08, "bottom": .14},
      plotting_options={SampleType.background: "hist", SampleType.signal: signal_options,
                        SampleType.data: "nostack e"},
    )
    plotter = HistogramPlotter(config)
    for source in backgrounds:
      plotter.stacks[SampleType.background][spec.getName()].Add(source)
    for source in signals:
      plotter.stacks[SampleType.signal][spec.getName()].Add(source)
    canvas = ROOT.TCanvas("range_canvas_%d" % next(self.identifiers), "", 800, 600)
    self.canvases.append(canvas)
    plotter._HistogramPlotter__setup_canvas(canvas, spec)
    plotter._HistogramPlotter__drawHists(canvas, spec)
    plotter._HistogramPlotter__drawUncertainties(canvas, spec)
    plotter._HistogramPlotter__drawSignalUncertainties(canvas, spec)
    pad = canvas.cd(1)
    legend = ROOT.TLegend(.70, .20, .98, .90)
    for source in backgrounds + list(signals):
      legend.AddEntry(source, "Sample", "l")
    legend.Draw()
    sources = plotter._HistogramPlotter__getPlottedHistograms(spec)
    first_stack = next(plotter.stacks[sample_type][spec.getName()] for sample_type in SampleType
                       if plotter.stacks[sample_type][spec.getName()].GetNhists() > 0)
    plotter.styler.adjustAxesForLegend(
      first_stack, spec, sources, [legend], pad,
      error_histograms=plotter._HistogramPlotter__getPlottedHistograms(spec, errors_only=True),
    )
    pad.Modified()
    pad.Update()
    self.objects.extend([plotter, legend])
    return plotter, pad, sources

  def test_signal_overlays_use_drawn_upper_errors_with_twenty_percent_padding(self):
    for options in ("nostack hist", "NOSTACK HIST", "nostackb", "nostack e"):
      with self.subTest(options=options):
        spec = Histogram("overlay_range_%d" % next(self.identifiers), x_min=0, x_max=6)
        backgrounds = [self.source([0, 2, 4, 6], [10e9, 5e9, 1e9])]
        signals = [self.source([0, 2, 4, 6], [peak * 1e9, 1e9, 1e9])
                   for peak in (56, 30, 24, 18, 12, 8, 6, 4)]
        if options != "nostack e":
          signals[0].SetBinError(1, 1e15)
        plotter, pad, sources = self.draw_plotter_stacks(spec, backgrounds, signals, options)
        # Eight overlaid signals have no visible cumulative sum.
        self.assertEqual(len(sources), len(signals) + len(backgrounds) + 1)
        upper = 56e9 + (.15 * 56e9 if options == "nostack e" else 0)
        self.assertAlmostEqual(pad.GetUymax(), 1.2 * upper, delta=1e3)
        errors = plotter._HistogramPlotter__getPlottedHistograms(spec, errors_only=True)
        self.assertEqual(len(errors), 1 + (len(signals) if options == "nostack e" else 0))

  def test_signal_stat_uncertainties_are_optional(self):
    spec = Histogram("optional_signal_errors_%d" % next(self.identifiers), x_min=0, x_max=2)
    signal = self.source([0, 1, 2], [20, 10])
    signal.SetBinError(2, 50)
    plotter, pad, _ = self.draw_plotter_stacks(spec, [], [signal])
    self.assertFalse(plotter.signal_uncertainties.get(spec.getName()))
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * 20)

  def test_signal_stat_uncertainties_preserve_separate_lines_and_upper_errors(self):
    spec = Histogram("signal_errors_%d" % next(self.identifiers), x_min=0, x_max=2)
    signals = [self.source([0, 1, 2], [20, 10]), self.source([0, 1, 2], [15, 6])]
    signals[0].SetBinError(2, 50)
    for source, color in zip(signals, (ROOT.kRed, ROOT.kGreen + 2)):
      source.SetLineColor(color)
      source.SetLineWidth(3)
    original_errors = [[source.GetBinError(index) for index in (1, 2)] for source in signals]
    plotter, pad, _ = self.draw_plotter_stacks(
      spec, [], signals, show_signal_stat_uncertainty=True)
    graphs = plotter.signal_uncertainties[spec.getName()]
    self.assertEqual(len(graphs), 2)
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (10 + 50))
    for graph, source, errors in zip(graphs, signals, original_errors):
      self.assertEqual(graph.GetLineColor(), source.GetLineColor())
      self.assertEqual(graph.GetLineWidth(), source.GetLineWidth())
      self.assertEqual(graph.GetMarkerSize(), 0)
      self.assertIn(graph, list(pad.GetListOfPrimitives()))
      for point, expected_error in enumerate(errors):
        self.assertEqual(graph.GetPointY(point), source.GetBinContent(point + 1))
        self.assertEqual(graph.GetErrorXlow(point), 0)
        self.assertEqual(graph.GetErrorXhigh(point), 0)
        self.assertEqual(graph.GetErrorYlow(point), expected_error)
        self.assertEqual(graph.GetErrorYhigh(point), expected_error)
        self.assertEqual(source.GetBinError(point + 1), expected_error)

  def test_signal_stat_uncertainties_use_asymmetric_and_weighted_bin_errors(self):
    for poisson in (False, True):
      with self.subTest(poisson=poisson):
        spec = Histogram("signal_bin_errors_%d" % next(self.identifiers), x_min=0, x_max=2)
        signal = self.source([0, 1, 2], [1, 3])
        if poisson:
          signal.Sumw2(False)
          signal.SetBinErrorOption(ROOT.TH1.kPoisson)
          self.assertGreater(signal.GetBinErrorUp(2), signal.GetBinErrorLow(2))
        else:
          signal.Reset()
          signal.Fill(.5, 2)
          signal.Fill(.5, 3)
          signal.Fill(1.5, 4)
          signal.Scale(2)
          self.assertAlmostEqual(signal.GetBinError(1), 2 * hypot(2, 3))
        plotter, _, _ = self.draw_plotter_stacks(
          spec, [], [signal], show_signal_stat_uncertainty=True)
        graph = plotter.signal_uncertainties[spec.getName()][0]
        for point in range(2):
          self.assertAlmostEqual(graph.GetErrorYlow(point), signal.GetBinErrorLow(point + 1))
          self.assertAlmostEqual(graph.GetErrorYhigh(point), signal.GetBinErrorUp(point + 1))

  def test_signal_stat_uncertainties_do_not_duplicate_explicit_error_drawing(self):
    spec = Histogram("explicit_signal_errors_%d" % next(self.identifiers), x_min=0, x_max=2)
    signal = self.source([0, 1, 2], [20, 10])
    signal.SetBinError(2, 50)
    plotter, pad, _ = self.draw_plotter_stacks(
      spec, [], [signal], signal_options="nostack e", show_signal_stat_uncertainty=True)
    self.assertFalse(plotter.signal_uncertainties.get(spec.getName()))
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (10 + 50))

  def test_stacked_signal_stat_uncertainties_follow_cumulative_histograms(self):
    spec = Histogram("stacked_signal_errors_%d" % next(self.identifiers), x_min=0, x_max=2)
    signals = [self.source([0, 1, 2], [10, 4]), self.source([0, 1, 2], [5, 3])]
    plotter, pad, _ = self.draw_plotter_stacks(
      spec, [], signals, signal_options="hist", show_signal_stat_uncertainty=True)
    graphs = plotter.signal_uncertainties[spec.getName()]
    self.assertEqual(len(graphs), 2)
    self.assertEqual(graphs[0].GetPointY(0), 10)
    self.assertEqual(graphs[1].GetPointY(0), 15)
    expected_error = hypot(signals[0].GetBinError(1), signals[1].GetBinError(1))
    self.assertAlmostEqual(graphs[1].GetErrorYhigh(0), expected_error)
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (15 + expected_error))

  def test_automatic_y_max_includes_stacked_background_total(self):
    spec = Histogram("stack_range_%d" % next(self.identifiers))
    backgrounds = [self.source([0, 1, 2], [50, 10]), self.source([0, 1, 2], [40, 5])]
    _, pad, sources = self.draw_plotter_stacks(spec, backgrounds)
    self.assertEqual(len(sources), 3)
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (90 + hypot(.15 * 50, .15 * 40)))

  def test_automatic_y_max_includes_systematic_background_band(self):
    spec = Histogram("systematic_range_%d" % next(self.identifiers), error=.5)
    backgrounds = [self.source([0, 1, 2], [50, 10]), self.source([0, 1, 2], [40, 5])]
    _, pad, _ = self.draw_plotter_stacks(spec, backgrounds)
    upper_error = hypot(hypot(.15 * 50, .15 * 40), .5 * 90)
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (90 + upper_error))

  def test_log_y_range_keeps_small_stacked_components(self):
    spec = Histogram("log_stack_range_%d" % next(self.identifiers), log_y=True)
    backgrounds = [self.source([0, 1, 2], [1e8, 2e8]), self.source([0, 1, 2], [100, 200])]
    plotter, pad, sources = self.draw_plotter_stacks(spec, backgrounds)
    minimum, maximum = plotter.styler.getYAxisRangeForLayout(
      spec, sources, error_histograms=plotter._HistogramPlotter__getPlottedHistograms(spec, errors_only=True),
    )
    self.assertAlmostEqual(minimum, 70)
    self.assertAlmostEqual(maximum, 1.2 * (2e8 + 200 + hypot(.15 * 2e8, .15 * 200)))
    self.assertLess(10 ** pad.GetUymin(), 100)
    self.assertGreater(10 ** pad.GetUymax(), 2e8 + 200)

  def test_automatic_y_max_follows_upper_error_of_lower_content_bin(self):
    source = self.source([0, 1, 2], [100, 80])
    source.SetBinError(1, 5)
    source.SetBinError(2, 50)
    spec = Histogram("largest_upper_error")
    _, pad, _, _ = self.draw(source, spec)
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (80 + 50))

  def test_automatic_y_max_uses_asymmetric_upper_poisson_error(self):
    source = self.source([0, 1, 2], [1, 3])
    source.Sumw2(False)
    source.SetBinErrorOption(ROOT.TH1.kPoisson)
    self.assertGreater(source.GetBinErrorUp(2), source.GetBinError(2))
    self.assertGreater(source.GetBinErrorUp(2), source.GetBinErrorLow(2))
    spec = Histogram("poisson_upper_error")
    _, pad, _, _ = self.draw(source, spec)
    self.assertAlmostEqual(pad.GetUymax(), 1.2 * (3 + source.GetBinErrorUp(2)))

  def test_explicit_y_max_remains_exact_with_axis_exponent(self):
    source = self.source([0, 1, 2], [10e9, 20e9])
    spec = Histogram("explicit_y_max", y_max=50e9)
    _, pad, _, _ = self.draw(source, spec)
    self.assertEqual(self.styler.getYAxisRangeForLayout(spec, [source])[1], 50e9)
    self.assertAlmostEqual(pad.GetUymax(), 50e9, delta=1e3)

  def test_bottom_margin_is_per_plot_and_shared_other_margins_are_stable(self):
    numeric = self.source([0, 1, 2], [1e8, 2e8])
    categorical = self.source([-0.5, 0.5, 1.5], [1e8, 2e8], ["unmatched", "different mothers"])
    numeric_spec = Histogram("numeric", log_y=True, x_label="#chi^{2}")
    category_spec = Histogram("category", log_y=True, x_label="generator mother")
    _, first, _, _ = self.draw(numeric, numeric_spec)
    _, middle, _, _ = self.draw(categorical, category_spec)
    _, last, _, _ = self.draw(numeric, numeric_spec)
    self.assertLess(first.GetBottomMargin(), 0.20)
    self.assertGreater(middle.GetBottomMargin(), first.GetBottomMargin() + 0.10)
    self.assertAlmostEqual(last.GetBottomMargin(), first.GetBottomMargin())
    for getter in ("GetLeftMargin", "GetTopMargin", "GetRightMargin"):
      self.assertAlmostEqual(getattr(first, getter)(), getattr(middle, getter)())
      self.assertAlmostEqual(getattr(first, getter)(), getattr(last, getter)())

  def test_variable_bin_legend_extension_changes_rendered_pad(self):
    source = self.source([-2000, -500, -100, -20, 0], [1e5, 1e7, 1e11, 1e13])
    spec = Histogram("pz", log_y=True, x_label="p_{z} [GeV]", y_min=1)
    _, pad, stack, legend = self.draw(source, spec, with_legend=True)
    self.assertGreater(pad.GetUxmax(), 100)
    self.assertAlmostEqual(pad.GetUxmax(), stack.GetXaxis().GetXmax(), places=6)
    self.assertEqual(source.GetXaxis().GetBinUpEdge(source.GetNbinsX()), 0)
    self.assert_legend_clear(pad, source, legend)

  def test_fixed_upper_x_bound_requires_y_clearance(self):
    source = self.source([0, 1, 2, 4, 6, 8], [1e12, 8e11, 5e11, 8e11, 1e12])
    spec = Histogram("chi2", log_y=True, x_max=8, y_min=1e11, x_label="#chi^{2}")
    _, pad, _, legend = self.draw(source, spec, with_legend=True)
    self.assertAlmostEqual(pad.GetUxmax(), 8)
    self.assertGreater(pad.GetUymax(), 13)
    self.assert_legend_clear(pad, source, legend)

  def test_tall_mass_legend_extends_x_without_extreme_log_y(self):
    source = self.source([0, 1, 2, 4, 6, 8, 10], [1e8, 3e8, 1e9, 4e8, 2e8, 1e8])
    spec = Histogram("mass", log_y=True, x_max=10, allow_legend_x_extension=True,
                     x_label="m_{#mu#mu} [GeV]")
    _, pad, stack, legend = self.draw(source, spec, with_legend=True,
                                     legend_box=(0.58, 0.20, 0.90, 0.90))
    self.assertGreater(pad.GetUxmax(), 15)
    self.assertLess(pad.GetUymax() - pad.GetUymin(), 5)

    self.assert_legend_clear(pad, source, legend)
    ranges = (pad.GetUxmin(), pad.GetUxmax(), pad.GetUymin(), pad.GetUymax())
    self.styler.adjustAxesForLegend(stack, spec, [source], [legend], pad)
    pad.Modified()
    pad.Update()
    for actual, expected in zip((pad.GetUxmin(), pad.GetUxmax(), pad.GetUymin(), pad.GetUymax()), ranges):
      self.assertAlmostEqual(actual, expected, places=6)

  def test_empty_histogram_loading_does_not_invent_tiny_positive_bins(self):
    source = ROOT.TH1D("empty_source_%d" % next(self.identifiers), "", 10, 0, 10)
    source.SetDirectory(0)
    self.objects.append(source)
    hist = Histogram("empty")
    hist.load(SimpleNamespace(Get=lambda name: source))
    self.assertEqual(hist.entries, 0)
    self.assertEqual(source.GetEntries(), 0)
    self.assertEqual(source.Integral(), 0)
    self.assertFalse(hist.isGood())

  def test_legend_extension_keeps_mass_crop(self):
    source = self.source([0, 2, 4, 6, 8, 10, 12], [1, 2, 3, 4, 5, 100])
    hist = Histogram("mass_crop", x_max=10, allow_legend_x_extension=True)
    hist.load(SimpleNamespace(Get=lambda name: source))
    self.assertEqual(hist.hist.GetXaxis().GetXmax(), 10)
    self.assertEqual(hist.hist.Integral(), 15)

  def test_tall_left_legend_extends_lower_x(self):
    source = self.source([1, 2, 3, 4, 5], [1e8] * 4)
    spec = Histogram("left_legend", log_y=True)
    _, pad, _, legend = self.draw(source, spec, with_legend=True,
                                 legend_box=(0.16, 0.20, 0.48, 0.90))
    self.assertLess(pad.GetUxmin(), 0)
    self.assertLess(pad.GetUymax() - pad.GetUymin(), 3)
    self.assert_legend_clear(pad, source, legend)

  def test_tall_legend_with_log_x_extends_x(self):
    source = self.source([1, 2, 4, 8, 16], [1e8] * 4)
    spec = Histogram("log_x_legend", log_x=True, log_y=True)
    _, pad, _, legend = self.draw(source, spec, with_legend=True,
                                 legend_box=(0.58, 0.20, 0.90, 0.90))
    self.assertGreater(10 ** pad.GetUxmax(), 30)
    self.assertLess(pad.GetUymax() - pad.GetUymin(), 3)
    self.assert_legend_clear(pad, source, legend)

  def test_legend_clearance_keeps_mixed_bins_and_signed_error_envelopes(self):
    sources = [
      self.source([0, 1, 2, 3, 4], [1e8, 2e8, 3e8, 2e8]),
      self.source([0, 1, 2, 3, 4], [-8e8, 3e8, -8e8, 1e8]),
      self.source([0, 1, 3, 4], [2e8, 5e8, 2e8]),
      self.source([0.5, 1.5, 2.5, 3.5, 4.5], [5e8, 1e8, 6e8, 3e8]),
    ]
    # A negative weighted content can still have a positive error envelope.
    sources[1].SetBinError(1, 2e9)
    sources[1].SetBinError(3, 4e9)
    spec = Histogram("mixed_bins", log_y=True, y_min=1e7)
    _, pad, stack, _ = self.draw(sources[0], spec)
    for source in sources[1:]:
      source.Draw("same e2")
    self.styler.setupFigure(stack, spec, source_histograms=sources)
    legend = ROOT.TLegend(0.58, 0.35, 0.90, 0.90)
    legend.SetTextFont(43)
    legend.SetTextSize(22)
    for index, source in enumerate(sources):
      legend.AddEntry(source, "Sample %d" % index, "f")
    legend.Draw()
    self.objects.append(legend)
    self.styler.adjustAxesForLegend(stack, spec, sources, [legend], pad)
    pad.Modified()
    pad.Update()
    for source in sources:
      self.assert_legend_clear(pad, source, legend)
    self.assertEqual([source.GetNbinsX() for source in sources], [4, 4, 3, 4])
    self.assertEqual(sources[1].GetBinContent(3), -8e8)
    self.assertEqual(sources[1].GetBinError(3), 4e9)

  def test_categorical_detection_ignores_empty_label_lists_and_cleared_labels(self):
    source = self.source([0, 1, 2], [1, 2])
    self.assertFalse(source.GetXaxis().GetLabels())
    self.assertEqual(self.styler.categoricalLabels([source]), [])
    source.GetXaxis().SetBinLabel(2, "second")
    self.assertEqual(self.styler.categoricalLabels([source]), [(1.5, "second")])
    source.GetXaxis().SetBinLabel(2, "")
    self.assertTrue(source.GetXaxis().GetLabels())
    self.assertEqual(self.styler.categoricalLabels([source]), [])

  def test_broad_log_distribution_does_not_gain_decades_for_tall_legend(self):
    source = self.source([0, 4000, 8000, 12000, 16000, 20000], [1e2, 1e9, 1e10, 1e10, 1e9])
    spec = Histogram("vz", log_y=True, x_label="v_{z} [cm]")
    _, pad, _, legend = self.draw(source, spec, with_legend=True,
                                 legend_box=(0.58, 0.20, 0.90, 0.90))
    self.assertGreater(pad.GetUxmax(), 30000)
    self.assertGreater(pad.GetUymin(), 0)
    self.assertLess(pad.GetUymax(), 13)
    self.assert_legend_clear(pad, source, legend)

  def test_fixed_x_with_tall_legend_keeps_bounded_y_and_warns(self):
    source = self.source([0, 2, 4, 6, 8, 10], [1e8, 3e8, 1e9, 4e8, 2e8])
    spec = Histogram("fixed_mass", log_y=True, x_min=0, x_max=10)
    from unittest.mock import patch
    with patch("Styler.warn") as warning:
      _, pad, _, _ = self.draw(source, spec, with_legend=True,
                               legend_box=(0.58, 0.20, 0.90, 0.90))
    warning.assert_called_once()
    self.assertAlmostEqual(pad.GetUxmax(), 10)
    self.assertLess(pad.GetUymax() - pad.GetUymin(), 5)

  def test_category_labels_follow_physical_bin_centers_after_x_expansion(self):
    labels = ["unmatched", "different mothers", "pion", "kaon", "other"]
    source = self.source([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], [1e12] * 5, labels)
    spec = Histogram("pid", log_y=True, y_min=1e4, x_label="generator mother")
    _, pad, stack, legend = self.draw(source, spec, with_legend=True)
    self.styler.drawCategoricalAxis(stack, spec, [source], pad)
    pad.Modified()
    pad.Update()
    texts = {
      str(item.GetTitle()): item for item in pad.GetListOfPrimitives()
      if item.InheritsFrom("TLatex") and str(item.GetTitle()) in labels
    }
    self.assertEqual(set(texts), set(labels))
    self.assertGreater(pad.GetUxmax(), 4.5)
    self.assert_legend_clear(pad, source, legend)
    for index, label in enumerate(labels, 1):
      expected_pixel = pad.XtoAbsPixel(source.GetBinCenter(index))
      label_pixel = pad.UtoAbsPixel(texts[label].GetX())
      self.assertLessEqual(abs(expected_pixel - label_pixel), 1, label)
    self.assertEqual(source.GetXaxis().GetXmax(), 4.5)

  def test_pdf_exports_fit_the_page_and_preserve_canvas_aspect_and_global_style(self):
    converter = shutil.which("pdftoppm")
    if converter is None:
      self.skipTest("pdftoppm is required for rendered-PDF verification")
    try:
      from PIL import Image
    except ImportError:
      self.skipTest("Pillow is required for rendered-PDF verification")
    with tempfile.TemporaryDirectory() as directory:
      config = SimpleNamespace(histograms=[], samples=[], output_path=directory,
                               show_ratio_plots=False)
      plotter = HistogramPlotter(config)
      previous_width, previous_height = array("f", [0.]), array("f", [0.])
      ROOT.gStyle.GetPaperSize(previous_width, previous_height)
      self.addCleanup(ROOT.gStyle.SetPaperSize, previous_width[0], previous_height[0])
      ROOT.gStyle.SetPaperSize(13., 17.)
      original_error_level = ROOT.gErrorIgnoreLevel
      for dimensions in ((1400, 850), (1200, 850), (600, 800)):
        with self.subTest(dimensions=dimensions):
          canvas = ROOT.TCanvas(f"pdf_canvas_{next(self.identifiers)}", "", *dimensions)
          self.canvases.append(canvas)
          canvas.SetFillColor(ROOT.kRed)
          path = Path(directory) / ("page_%d_%d.pdf" % dimensions)
          plotter._HistogramPlotter__save_canvas(canvas, str(path))
          paper_width, paper_height = array("f", [0.]), array("f", [0.])
          ROOT.gStyle.GetPaperSize(paper_width, paper_height)
          self.assertEqual((paper_width[0], paper_height[0]), (13., 17.))
          self.assertEqual(ROOT.gErrorIgnoreLevel, original_error_level)
          subprocess.run([converter, "-r", "50", "-png", "-singlefile", str(path),
                          str(path.with_suffix(""))], check=True, capture_output=True)
          with Image.open(path.with_suffix(".png")) as exported:
            image = exported.convert("RGB")
            red_pixels = [(index % image.width, index // image.width)
                          for index, color in enumerate(image.getdata())
                          if color[0] > 200 and color[1] < 100 and color[2] < 100]
            left = min(x for x, y in red_pixels)
            top = min(y for x, y in red_pixels)
            width = max(x for x, y in red_pixels) - left + 1
            height = max(y for x, y in red_pixels) - top + 1
            self.assertLess(left / image.width, .10)
            self.assertLess(top / image.height, .12)
            self.assertGreater(width / image.width, .85)
            self.assertGreater(height / image.height, .75)
            self.assertAlmostEqual(width / height, canvas.GetWw() / canvas.GetWh(), delta=.015)

  def test_batch_exports_keep_last_canvas_legends_and_header(self):
    try:
      from PIL import Image
    except ImportError:
      self.skipTest("Pillow is required for exported-image verification")
    with tempfile.TemporaryDirectory() as directory:
      specifications = [Histogram(f"export_{index}", norm_type=NormalizationType.none, log_y=True,
                                  x_label="observable", y_label="entries") for index in range(3)]
      samples = [Sample(name="background", type=SampleType.background,
                        legend_description="background", fill_color=ROOT.kBlue),
                 Sample(name="signal", type=SampleType.signal,
                        legend_description="signal", line_color=ROOT.kRed)]
      config = SimpleNamespace(
        histograms=specifications, samples=samples, output_path=directory,
        output_formats=["png"], canvas_size=(800, 600), show_ratio_plots=False,
        show_signal_stat_uncertainty=True,
        show_cms_labels=True, cms_label=CmsLabel.pas_sim, label_outside_axes=True,
        luminosity=1., beam_label="simulation", auto_adjust_axes_for_legend=True,
        plot_margins={"left": .10, "right": .37, "top": .12, "bottom": .14},
        legends={SampleType.background: Legend(.65, .48, .99, .90, "f"),
                 SampleType.signal: Legend(.65, .12, .99, .45, "l")},
        plotting_options={SampleType.background: "hist", SampleType.signal: "nostack hist",
                          SampleType.data: "nostack e"},
      )
      plotter = HistogramPlotter(config)
      for spec in specifications:
        for sample in samples:
          source = self.source([0, 2, 4, 6], [10, 20, 30])
          source.SetEntries(3)
          histogram = Histogram(spec.name, norm_type=NormalizationType.none, log_y=True,
                                x_label=spec.x_label, y_label=spec.y_label)
          histogram.set_hist(source)
          plotter.histosamples.append((histogram, sample))
      plotter.setupLegends()
      plotter.buildStacks()
      plotter.drawStacks()
      for spec in specifications:
        self.assertEqual(len(plotter.signal_uncertainties[spec.getName()]), 1)
        with Image.open(Path(directory) / (spec.name + ".png")) as exported:
          image = exported.convert("RGB")
          width, height = image.size
          legends = image.crop((int(.66 * width), int(.14 * height), width, int(.91 * height)))
          header = image.crop((int(.08 * width), int(.02 * height), int(.63 * width), int(.105 * height)))
          dark_pixels = lambda region: sum(max(pixel) < 220 for pixel in region.getdata())
          self.assertGreater(dark_pixels(legends), 100, spec.name + " legends")
          self.assertGreater(dark_pixels(header), 100, spec.name + " header")


if __name__ == "__main__":
  unittest.main()
