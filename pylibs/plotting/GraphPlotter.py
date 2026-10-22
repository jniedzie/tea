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
