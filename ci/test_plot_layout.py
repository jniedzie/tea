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

  def draw(self, source, spec, with_legend=False):
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
      legend = ROOT.TLegend(0.68, 0.60, 0.93, 0.90)
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
    for index in range(1, source.GetNbinsX() + 1):
      x1 = source.GetXaxis().GetBinLowEdge(index)
      x2 = source.GetXaxis().GetBinUpEdge(index)
      if x2 <= pad.GetUxmin() or x1 >= pad.GetUxmax():
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
    spec = Histogram("chi2", log_y=True, x_max=8, y_min=1e4, x_label="#chi^{2}")
    _, pad, _, legend = self.draw(source, spec, with_legend=True)
    self.assertAlmostEqual(pad.GetUxmax(), 8)
    self.assertGreater(pad.GetUymax(), 13)
    self.assert_legend_clear(pad, source, legend)

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
