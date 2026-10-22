"""Reusable ROOT Brazil plots. Imports neither ROOT nor analysis configuration until requested."""

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence, Tuple
import uuid
import warnings

from LimitPoint import LimitPoint, finite_number, scale_point, validate_collection


@dataclass
class PlotOptions:
  x_title: str = "x"
  y_title: str = "95% CL upper limit on r"
  x_unit: str = ""
  y_unit: str = ""
  x_range: Optional[Tuple[float, float]] = None
  y_range: Optional[Tuple[float, float]] = None
  log_x: bool = False
  log_y: bool = False
  tick_labels: Mapping[float, str] = field(default_factory=dict)
  y_tick_labels: Mapping[float, str] = field(default_factory=dict)
  legend_bounds: Tuple[float, float, float, float] = (0.20, 0.66, 0.52, 0.89)
  luminosity: Optional[float] = None  # fb^-1
  collision_energy: str = "13 TeV"
  experiment_label: str = "#bf{CMS} #it{Preliminary}"
  annotations: Sequence[str] = ()
  show_observed: bool = False
  quantity: str = "r"
  constant_scale: Optional[float] = None
  reference: Optional[str] = None  # 'r1' or 'nominal'; expressed in the selected quantity


def prepare_segments(points: Sequence[LimitPoint], options: PlotOptions) -> list:
  """Sort numeric x and split at explicitly missing points; never invent or interpolate them."""
  points = sorted(validate_collection(points), key=lambda point: point.x)
  xs = [point.x for point in points]
  if len(xs) != len(set(xs)):
    raise ValueError("Multiple points share x; select a fixed-parameter slice before plotting")
  segments, current = [], []
  for point in points:
    if options.log_x and point.x <= 0:
      raise ValueError(f"{point.id}: log x requires positive x")
    if point.status != "ok":
      warnings.warn(f"{point.id}: {point.status}: {point.message}", RuntimeWarning, stacklevel=2)
      if current:
        segments.append(current)
        current = []
      continue
    current.append(scale_point(point, options.quantity, options.constant_scale))
  if current:
    segments.append(current)
  return segments


def _range(values: list, specified: Optional[tuple], logarithmic: bool) -> tuple:
  if specified is not None:
    low, high = [finite_number(value, "axis range") for value in specified]
  else:
    low, high = min(values), max(values)
    if logarithmic:
      low, high = low / 1.4, high * 1.4
    else:
      margin = (high - low) * 0.12 if high != low else max(abs(low) * 0.12, 0.1)
      low, high = low - margin, high + margin
  if low >= high or (logarithmic and low <= 0):
    raise ValueError("Axis bounds must be increasing and positive for a logarithmic scale")
  return low, high


def plot_limits(points: Sequence[LimitPoint], options: Optional[PlotOptions] = None):
  """Return a ROOT canvas retaining all graphs; caller controls saving and ROOT batch mode."""
  options = options or PlotOptions()
  if options.reference not in (None, "r1", "nominal"):
    raise ValueError("reference must be None, 'r1', or 'nominal'")
  segments = prepare_segments(points, options)
  valid = [point for segment in segments for point in segment]
  if not valid:
    raise ValueError("No valid limit points to plot")
  references = {}
  for point in valid:
    if options.reference == "r1":
      references[point.id] = (
        1.0
        if options.quantity == "r"
        else (options.constant_scale if options.constant_scale is not None else point.nominal_cross_section)
      )
    elif options.reference == "nominal":
      if point.nominal_cross_section is None:
        raise ValueError(f"{point.id}: nominal_cross_section required for nominal reference")
      references[point.id] = point.nominal_cross_section if options.quantity == "cross_section" else 1.0
    if options.reference and references[point.id] is None:
      raise ValueError(f"{point.id}: nominal_cross_section required for r=1 reference in cross-section units")
  x_range = _range([point.x for point in points], options.x_range, options.log_x)
  ys = [value for point in valid for value in point.expected.values()]
  ys += [point.observed for point in valid if options.show_observed and point.observed is not None]
  ys += list(references.values())
  y_range = _range(ys, options.y_range, options.log_y)
  if options.y_range is None:
    # Keep automatic limits below the legend and annotations, including isolated bars.
    low, high = y_range
    high = low * (high / low) ** 1.5 if options.log_y else low + (high - low) * 1.5
    y_range = (low, high)
  import ROOT

  canvas = ROOT.TCanvas(f"limits_{uuid.uuid4().hex}", "", 800, 600)
  canvas.SetLeftMargin(0.15)
  canvas.SetBottomMargin(0.15)
  canvas.SetLogx(options.log_x)
  canvas.SetLogy(options.log_y)
  frame = canvas.DrawFrame(x_range[0], y_range[0], x_range[1], y_range[1])
  frame.GetXaxis().SetTitle(options.x_title + (f" [{options.x_unit}]" if options.x_unit else ""))
  frame.GetYaxis().SetTitle(options.y_title + (f" [{options.y_unit}]" if options.y_unit else ""))
  retained = [frame]
  if options.tick_labels:
    frame.GetXaxis().SetLabelSize(0)
    for x, label in options.tick_labels.items():
      text = ROOT.TLatex(float(x), y_range[0], str(label))
      text.SetTextAlign(23)
      text.SetTextSize(0.035)
      text.Draw()
      retained.append(text)
  if options.y_tick_labels:
    frame.GetYaxis().SetLabelSize(0)
    for y, label in options.y_tick_labels.items():
      text = ROOT.TLatex(x_range[0], float(y), str(label))
      text.SetTextAlign(32)
      text.SetTextSize(0.035)
      text.Draw()
      retained.append(text)
  handles = {}
  for segment in segments:
    for lower, upper, color, title in (
      (0.025, 0.975, ROOT.kYellow + 1, "Expected #pm 2 #sigma"),
      (0.16, 0.84, ROOT.kGreen + 1, "Expected #pm 1 #sigma"),
    ):
      graph = ROOT.TGraphAsymmErrors()
      graph.SetFillColor(color)
      graph.SetLineColor(color)
      graph.SetLineWidth(6 if lower == 0.025 else 3)
      graph.SetMarkerStyle(20)
      for i, point in enumerate(segment):
        median = point.expected[0.5]
        graph.SetPoint(i, point.x, median)
        graph.SetPointError(i, 0, 0, median - point.expected[lower], point.expected[upper] - median)
      # Vertical asymmetric bars remain visible for isolated points, whose band has zero width.
      graph.Draw("Z SAME" if len(segment) == 1 else "3 SAME")
      retained.append(graph)
      handles[title] = graph
    for observed in (False, True):
      if observed and not options.show_observed:
        continue
      # Missing observed values also break the observed curve.
      groups, group = [], []
      for point in segment:
        if observed and point.observed is None:
          if group:
            groups.append(group)
            group = []
        else:
          group.append(point)
      if group:
        groups.append(group)
      for group in groups:
        graph = ROOT.TGraph()
        graph.SetLineWidth(2)
        graph.SetLineStyle(1 if observed else 2)
        graph.SetMarkerStyle(20)
        for i, point in enumerate(group):
          graph.SetPoint(i, point.x, point.observed if observed else point.expected[0.5])
        graph.Draw("LP SAME")
        retained.append(graph)
        handles["Observed" if observed else "Expected"] = graph
    if references:
      graph = ROOT.TGraph()
      graph.SetLineColor(ROOT.kRed + 1)
      graph.SetLineWidth(2)
      graph.SetMarkerStyle(24)
      for i, point in enumerate(segment):
        graph.SetPoint(i, point.x, references[point.id])
      graph.Draw("LP SAME")
      retained.append(graph)
      handles[
        "r = 1"
        if options.reference == "r1"
        else ("Nominal cross section" if options.quantity == "cross_section" else "Nominal (r = 1)")
      ] = graph
  legend = ROOT.TLegend(*options.legend_bounds)
  legend.SetBorderSize(0)
  legend.SetFillStyle(0)
  for title, graph in handles.items():
    legend.AddEntry(graph, title, "F" if "sigma" in title else "LP")
  legend.Draw()
  retained.append(legend)
  labels = [(0.15, 0.93, options.experiment_label)]
  lumi = "" if options.luminosity is None else f"{options.luminosity:g} fb^{{-1}} "
  labels.append((0.60, 0.93, lumi + options.collision_energy))
  labels.extend((0.56, 0.85 - 0.05 * i, text) for i, text in enumerate(options.annotations))
  for x, y, title in labels:
    text = ROOT.TLatex(x, y, title)
    text.SetNDC()
    text.SetTextSize(0.035)
    text.Draw()
    retained.append(text)
  canvas.RedrawAxis()
  canvas.Update()
  canvas._limit_objects = retained
  canvas._limit_segments = segments
  return canvas
