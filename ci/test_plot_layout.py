#!/usr/bin/env python3
"""ROOT rendering regressions; run with a Python environment providing PyROOT."""

from array import array
from itertools import count
from pathlib import Path
import sys
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


if __name__ == "__main__":
  unittest.main()
