#!/usr/bin/env python3
"""Rendered categorical labels and an external legend retain data coordinates."""

import ctypes
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


@unittest.skipIf(ROOT is None, "PyROOT is required")
class CategoricalLegendLayoutTest(unittest.TestCase):
  identifiers = count()

  def setUp(self):
    self.objects = []
    self.canvases = []
    self.styler = Styler(SimpleNamespace(
      categorical_legend_outside=True, auto_adjust_axes_for_legend=True,
    ))
    self.styler.configureAutomaticMargins([(1e-30, 1e30)], (800, 600))

  def tearDown(self):
    for canvas in self.canvases:
      canvas.Close()

  def draw_category(self):
    identifier = next(self.identifiers)
    canvas = ROOT.TCanvas(f"category_canvas_{identifier}", "", 1200, 850)
    self.canvases.append(canvas)
    source = ROOT.TH1D(f"category_source_{identifier}", "", 34, -32.5, 1.5)
    source.SetDirectory(0)
    labels = {
      -32: "-32: invalid charge", -31: "-31: transport call limit",
      -30: "-30: invalid derivative", -4: "-4: no convergence",
      -3: "-3: invalid covariance/update", -1: "-1: missing detector state",
      0: "0: disabled/unpaired", 1: "1: valid",
    }
    for value, label in labels.items():
      index = source.FindFixBin(value)
      source.GetXaxis().SetBinLabel(index, label)
      source.SetBinContent(index, 1e10 + (value + 32) * 1e9)
    spec = Histogram("status", log_y=True, x_label="joint vertex refit status", y_label="# dimuons")
    legend = ROOT.TLegend(0.58, 0.2, 0.9, 0.9)
    legend.SetTextFont(43)
    legend.SetTextSize(16)
    for index in range(19):
      legend.AddEntry(source, f"Sample {index}: m_{{#mu#mu}}^{{gen}} #in [0.211317, 0.5] GeV", "f")
    self.styler.preparePlotLayout(spec, [source], canvas, legends=[legend])
    canvas.Divide(1, 1)
    pad = canvas.cd(1)
    self.styler.setup_main_pad_without_ratio(pad, True)
    pad.SetLogy(True)
    stack = ROOT.THStack(f"category_stack_{identifier}", "")
    stack.Add(source)
    self.styler.prepareDisplayFrame(stack)
    stack.Draw("hist")
    self.styler.setupFigure(stack, spec, source_histograms=[source])
    legend.Draw()
    self.styler.adjustAxesForLegend(stack, spec, [source], [legend], pad)
    self.styler.drawCategoricalAxis(stack, spec, [source], pad)
    pad.Modified()
    pad.Update()
    self.objects.extend([source, stack, legend])
    return source, labels, pad, legend

  def test_full_status_axis_and_readable_legend_do_not_overlap(self):
    source, labels, pad, legend = self.draw_category()
    self.assertEqual(source.GetNbinsX(), 34)
    self.assertEqual((source.GetXaxis().GetXmin(), source.GetXaxis().GetXmax()), (-32.5, 1.5))
    self.assertAlmostEqual(pad.GetUxmin(), -32.5)
    self.assertAlmostEqual(pad.GetUxmax(), 1.5)
    self.assertEqual(legend.GetTextSize(), 16)
    self.assertEqual(legend.GetListOfPrimitives().GetSize(), 19)
    self.assertLess(pad.GetLeftMargin(), 0.15)
    legend_left = pad.UtoAbsPixel(legend.GetX1NDC())
    texts = {
      str(item.GetTitle()): item for item in pad.GetListOfPrimitives()
      if item.InheritsFrom("TLatex") and str(item.GetTitle()) in labels.values()
    }
    self.assertEqual(set(texts), set(labels.values()))
    for value, label in labels.items():
      text = texts[label]
      text_pixel = pad.UtoAbsPixel(text.GetX())
      self.assertLessEqual(abs(text_pixel - pad.XtoAbsPixel(value)), 1, label)
      horizontal_extent = ctypes.c_uint()
      vertical_extent = ctypes.c_uint()
      text.GetBoundingBox(horizontal_extent, vertical_extent, True)
      self.assertLess(text_pixel + horizontal_extent.value / 2, legend_left, label)

  def test_continuous_layout_is_restored_after_categorical_plot(self):
    before = tuple(self.styler.sharedLayoutMargins[key] for key in ("left", "right", "top"))
    self.draw_category()
    canvas = ROOT.TCanvas("after_category_canvas", "", 800, 600)
    self.canvases.append(canvas)
    source = ROOT.TH1D("after_category_source", "", 10, 0, 10)
    source.SetDirectory(0)
    self.objects.append(source)
    self.styler.preparePlotLayout(Histogram("numeric", log_y=True), [source], canvas)
    after = (self.styler.leftMargin, self.styler.rightMargin, self.styler.topMargin)
    self.assertEqual(after, before)


if __name__ == "__main__":
  unittest.main()
