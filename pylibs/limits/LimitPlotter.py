"""Reusable ROOT Brazil plots. Imports neither ROOT nor analysis configuration until requested."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple
from types import SimpleNamespace
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
  legend_bounds: Optional[Tuple[float, float, float, float]] = None
  canvas_size: Tuple[int, int] = (800, 600)
  plot_margins: Optional[Mapping[str, float]] = None
  cms_label: Any = "pas"
  label_outside_axes: bool = True
  luminosity: Optional[float] = None  # fb^-1
  collision_energy: str = "13 TeV"
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


def plot_limits(points: Sequence[LimitPoint], options: Optional[PlotOptions] = None, plot_config: Any = None):
  """Add limit content to TEA's shared graph presentation; return its ROOT canvas.

  ``plot_config`` optionally supplies the same style/Legend/CmsLabel settings as
  the normal histogram plotter. Importing this module still has no ROOT or I/O effects.
  """
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
  for bounds, logarithmic in ((options.x_range, options.log_x), (options.y_range, options.log_y)):
    if bounds is not None:
      low, high = (finite_number(value, "axis range") for value in bounds)
      if low >= high or (logarithmic and low <= 0):
        raise ValueError("Axis bounds must be increasing and positive for a logarithmic scale")
  import ROOT
  from GraphPlotter import draw_graphs
  from Histogram import Histogram
  from CmsLabelsManager import CmsLabel
  from Legend import Legend

  definition = Histogram(
    name="limits",
    log_x=options.log_x,
    log_y=options.log_y,
    x_min=options.x_range[0] if options.x_range else None,
    x_max=options.x_range[1] if options.x_range else None,
    y_min=options.y_range[0] if options.y_range else None,
    y_max=options.y_range[1] if options.y_range else None,
    x_label=options.x_title + (f" [{options.x_unit}]" if options.x_unit else ""),
    y_label=options.y_title + (f" [{options.y_unit}]" if options.y_unit else ""),
  )
  definition.x_values = [point.x for point in points]
  config = SimpleNamespace(
    canvas_size=options.canvas_size,
    plot_margins=options.plot_margins,
    show_cms_labels=True,
    cms_label=CmsLabel[options.cms_label] if isinstance(options.cms_label, str) else options.cms_label,
    label_outside_axes=options.label_outside_axes,
    show_ratio_plots=False,
    beam_label=options.collision_energy,
    auto_adjust_axes_for_legend=True,
    annotations=options.annotations,
  )
  if options.luminosity is not None:
    config.lumi_label_value = options.luminosity * 1000
  if options.legend_bounds is not None:
    config.legend = Legend(*options.legend_bounds)
  if plot_config is not None:
    vars(config).update(vars(plot_config))
    config.show_ratio_plots = False
  graphs = []
  handles = {}
  for segment in segments:
    for lower, upper, color, title in (
      (0.025, 0.975, ROOT.kYellow, "Expected #pm 2 #sigma"),
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
      graphs.append((graph, "Z" if len(segment) == 1 else "3"))
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
        graph.SetLineColor(ROOT.kBlack)
        graph.SetLineWidth(2)
        graph.SetLineStyle(1 if observed else 2)
        graph.SetMarkerStyle(20)
        for i, point in enumerate(group):
          graph.SetPoint(i, point.x, point.observed if observed else point.expected[0.5])
        graphs.append((graph, "LP" if len(group) == 1 else "L"))
        handles["Observed" if observed else "Expected"] = graph
    if references:
      graph = ROOT.TGraph()
      graph.SetLineColor(ROOT.kRed + 1)
      graph.SetLineWidth(2)
      graph.SetMarkerStyle(24)
      for i, point in enumerate(segment):
        graph.SetPoint(i, point.x, references[point.id])
      graphs.append((graph, "P" if len(segment) == 1 else "L"))
      handles[
        "r = 1"
        if options.reference == "r1"
        else ("Nominal cross section" if options.quantity == "cross_section" else "Nominal (r = 1)")
      ] = graph
  order = ("Observed", "Expected", "Expected #pm 1 #sigma", "Expected #pm 2 #sigma")
  titles = [title for title in order if title in handles] + [title for title in handles if title not in order]
  entries = [(handles[title], title, "F" if "sigma" in title else "L") for title in titles]
  canvas = draw_graphs(graphs, definition, config, entries)
  canvas._limit_objects = canvas._plot_objects
  canvas._limit_segments = segments
  return canvas
