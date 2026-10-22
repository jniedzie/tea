"""ROOT graph presentation using the same layout, labels and legends as HistogramPlotter."""

from typing import Any, Sequence
import uuid


def draw_graphs(
  graphs: Sequence[tuple[Any, str]], definition: Any, config: Any, legend_entries: Sequence[tuple[Any, str, str]]
) -> Any:
  """Draw physical graph coordinates; ``definition`` follows Histogram's axis fields.

  ``config`` uses TEA's normal canvas_size, plot_margins, cms_label,
  label_outside_axes, lumi_label_value (pb^-1), beam_label and Legend settings.
  No samples, normalization or files are required.
  """
  import ROOT
  from Styler import Styler
  from CmsLabelsManager import CmsLabelsManager
  from Legend import Legend

  sources = [graph for graph, _ in graphs]
  styler = Styler(config)
  labels = CmsLabelsManager(config)
  y_range = styler.getYAxisRangeForLayout(definition, sources)
  styler.configureAutomaticMargins([y_range], config.canvas_size, [definition.x_label])
  canvas = ROOT.TCanvas(f"graphs_{uuid.uuid4().hex}", "", *config.canvas_size)
  canvas.cd()
  legend_spec = getattr(config, "legend", None) or Legend(0.60, 0.64, 0.94, 0.90)
  legend = legend_spec.getRootLegend()
  for annotation in getattr(config, "annotations", ()):
    legend.AddEntry(ROOT.nullptr, str(annotation), "")
  for graph, label, option in legend_entries:
    legend.AddEntry(graph, label, option)
  styler.preparePlotLayout(definition, sources, canvas, legends=[legend])
  canvas.Divide(1, 1)
  pad = canvas.cd(1)
  styler.setup_main_pad_without_ratio(pad)
  pad.SetLogx(definition.log_x)
  pad.SetLogy(definition.log_y)
  plot = ROOT.TMultiGraph()
  for graph, option in graphs:
    plot.Add(graph, option)
    ROOT.SetOwnership(graph, False)  # TMultiGraph owns its graphs.
  plot.Draw("A")
  styler.setupFigure(plot, definition, source_histograms=sources)
  legend.Draw()
  styler.adjustAxesForLegend(plot, definition, sources, [legend], pad)
  pad.Update()
  _draw_tick_labels(plot, pad, getattr(config, "x_tick_labels", {}), "x", styler.labelFontSize)
  _draw_tick_labels(plot, pad, getattr(config, "y_tick_labels", {}), "y", styler.labelFontSize)
  labels.drawLabels(pad, update=False)
  frame = pad.GetFrame()
  frame.SetLineWidth(1)
  frame.SetBorderSize(1)
  frame.SetBorderMode(0)
  frame.SetFillColor(0)
  frame.SetFillStyle(0)
  pad.RedrawAxis()
  pad.Modified()
  canvas.Modified()
  canvas.Update()
  canvas._plot_pad = pad
  canvas._plot_objects = [plot, legend, styler, labels, *sources]
  return canvas


def _draw_tick_labels(plot: Any, pad: Any, labels: Any, axis_name: str, font_size: int) -> None:
  if not labels:
    return
  import math
  import ROOT

  axis = plot.GetXaxis() if axis_name == "x" else plot.GetYaxis()
  axis.SetLabelSize(0)
  logarithmic = pad.GetLogx() if axis_name == "x" else pad.GetLogy()
  if axis_name == "x":
    minimum, maximum = axis.GetXmin(), axis.GetXmax()
    start, stop = pad.GetLeftMargin(), 1 - pad.GetRightMargin()
  else:
    minimum, maximum = pad.GetUymin(), pad.GetUymax()
    if logarithmic:
      minimum, maximum = 10**minimum, 10**maximum
    start, stop = pad.GetBottomMargin(), 1 - pad.GetTopMargin()
  transform = math.log10 if logarithmic else lambda x: x
  low, high = transform(minimum), transform(maximum)
  retained = getattr(pad, "_graph_tick_labels", [])
  for value, label in labels.items():
    if not minimum <= value <= maximum:
      continue
    position = start + (transform(value) - low) / (high - low) * (stop - start)
    text = ROOT.TLatex()
    text.SetNDC()
    text.SetTextFont(43)
    text.SetTextSize(font_size)
    if axis_name == "x":
      text.SetTextAlign(23)
      retained.append(text.DrawLatex(position, pad.GetBottomMargin() - 10 / pad.GetWh(), str(label)))
    else:
      text.SetTextAlign(32)
      retained.append(text.DrawLatex(pad.GetLeftMargin() - 10 / pad.GetWw(), position, str(label)))
  pad._graph_tick_labels = retained
