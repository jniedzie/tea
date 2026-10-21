from array import array
from copy import copy
from dataclasses import dataclass
from itertools import count
import math
from typing import Any

import ROOT

from HistogramNormalizer import NormalizationType
from Legend import Legend
from Logger import info, warn
from Sample import SampleType


_ids = count()


@dataclass(frozen=True)
class HistogramGroup2D:
  name: str
  samples: tuple[str, ...]
  legend_description: str
  palette: int = ROOT.kBird
  alpha: float = 0.6
  draw_heatmap: bool = True
  show_contours: bool | None = None
  contour_color: int | None = None

  def __post_init__(self) -> None:
    if not self.name or not self.samples or len(set(self.samples)) != len(self.samples):
      raise ValueError("A 2D group requires a name and a nonempty list of unique sample names")
    if not math.isfinite(self.alpha) or not 0 <= self.alpha <= 1:
      raise ValueError(f"Invalid opacity for 2D group '{self.name}'")
    if int(self.palette) != 1 and not 51 <= int(self.palette) <= 113:
      raise ValueError(f"Unsupported ROOT palette ID for 2D group '{self.name}': {self.palette}")
    if not isinstance(self.draw_heatmap, bool) or not (
      self.show_contours is None or isinstance(self.show_contours, bool)
    ):
      raise ValueError(f"Invalid drawing toggles for 2D group '{self.name}'")


def resolve_groups(config: Any, hist: Any) -> tuple[HistogramGroup2D, ...]:
  groups = tuple(getattr(config, "groups2D", ()) if hist.groups is None else hist.groups)
  if not all(isinstance(group, HistogramGroup2D) for group in groups):
    raise TypeError(f"Groups for '{hist.getName()}' must be HistogramGroup2D objects")
  if len({group.name for group in groups}) != len(groups):
    raise ValueError(f"Duplicate group names for '{hist.getName()}'")
  return groups


def clone_histogram(source: Any, label: str) -> Any:
  result = source.Clone(f"tea_grouped_{label}_{next(_ids)}")
  result.SetDirectory(0)
  return result


def axis_edges(axis: Any) -> tuple[float, ...]:
  return tuple(axis.GetBinLowEdge(index) for index in range(1, axis.GetNbins() + 2))


def displayed_bins(histogram: Any) -> list[tuple[int, int]]:
  return [
    (x, y)
    for x in range(histogram.GetXaxis().GetFirst(), histogram.GetXaxis().GetLast() + 1)
    for y in range(histogram.GetYaxis().GetFirst(), histogram.GetYaxis().GetLast() + 1)
    if 1 <= x <= histogram.GetNbinsX() and 1 <= y <= histogram.GetNbinsY()
  ]


def probability_regions(
  histogram: Any, fractions: tuple[float, ...], context: str
) -> tuple[Any, tuple[tuple[float, float, float], ...]]:
  if (
    not fractions
    or len(set(fractions)) != len(fractions)
    or any(not math.isfinite(value) or not 0 < value < 1 for value in fractions)
  ):
    raise ValueError(f"Contour fractions must be unique and strictly between 0 and 1: {context}")
  density = clone_histogram(histogram, "density")
  density.Reset()
  cells = []
  clipped = False
  for x, y in displayed_bins(histogram):
    content = histogram.GetBinContent(x, y)
    if not math.isfinite(content):
      raise ValueError(f"Nonfinite bin content: {context}")
    clipped |= content < 0
    weight = max(0.0, content)
    area = histogram.GetXaxis().GetBinWidth(x) * histogram.GetYaxis().GetBinWidth(y)
    value = weight / area
    density.SetBinContent(x, y, value)
    cells.append((value, weight))
  if clipped:
    warn(f"Negative bins clipped to zero for probability contours only: {context}")
  total = math.fsum(weight for _, weight in cells)
  if total <= 0:
    warn(f"No positive displayed weight; skipping probability contours: {context}")
    return density, ()
  ordered = sorted(cells, reverse=True)
  regions = []
  for fraction in fractions:
    cumulative = 0.0
    for threshold, weight in ordered:
      cumulative += weight
      if cumulative >= fraction * total:
        break
    achieved = math.fsum(weight for value, weight in cells if value >= threshold) / total
    regions.append((fraction, threshold, achieved))
    info(f"{context}: requested {fraction:.1%} contour encloses {achieved:.1%} of displayed positive weight")
  return density, tuple(regions)


class GroupedHistogram2DPlotter:
  def __init__(self, config: Any, styler: Any, normalizer: Any) -> None:
    self.config = config
    self.styler = styler
    self.normalizer = normalizer
    self.retained: list[Any] = []
    self.canvases: list[Any] = []

  def prepare_groups(self, hist: Any, objects: list[tuple[Any, Any]]) -> list[tuple[HistogramGroup2D, Any]]:
    groups = resolve_groups(self.config, hist)
    if hist.norm_type not in (NormalizationType.none, NormalizationType.to_lumi):
      raise ValueError(f"Grouped plot '{hist.getName()}' supports only to_lumi and none normalization")
    samples = {sample.name: sample for sample in self.config.samples}
    if len(samples) != len(self.config.samples):
      raise ValueError("Grouped plots require unique config sample names")
    sources = {(item.getName(), sample.name): item.hist for item, sample in objects}
    expected_edges = None
    result = []
    if hist.x_rebin < 1 or hist.y_rebin < 1 or int(hist.x_rebin) != hist.x_rebin or int(hist.y_rebin) != hist.y_rebin:
      raise ValueError(f"Rebin factors must be positive integers for '{hist.getName()}'")
    for group in groups:
      combined = None
      for name in group.samples:
        context = f"group '{group.name}', histogram '{hist.getName()}', dataset '{name}'"
        if name not in samples:
          raise ValueError(f"Unknown dataset: {context}")
        source = sources.get((hist.getName(), name))
        if source is None or not source or not source.InheritsFrom("TH2") or source.InheritsFrom("TProfile2D"):
          raise ValueError(f"Missing or invalid TH2 histogram: {context}")
        edges = (axis_edges(source.GetXaxis()), axis_edges(source.GetYaxis()))
        if expected_edges is not None and edges != expected_edges:
          raise ValueError(f"Incompatible x/y bin edges: {context}")
        expected_edges = edges
        member = copy(hist)
        member.hist = clone_histogram(source, "member")
        if not member.hist.GetSumw2N():
          member.hist.Sumw2()
        sample = samples[name]
        if hist.norm_type == NormalizationType.to_lumi and sample.type != SampleType.data:
          weights = (
            getattr(self.normalizer, "background_initial_sum_weights", {}).get((name, sample.year))
            if sample.type == SampleType.background
            else getattr(self.normalizer, "signal_initial_sum_weights", {}).get(name)
          )
          if weights is None or not math.isfinite(weights) or weights == 0:
            raise ValueError(f"Missing or zero initial sum of event weights: {context}")
          luminosity = sample.luminosity if sample.luminosity > 0 else getattr(self.config, "luminosity", None)
          if luminosity is None or not math.isfinite(luminosity) or luminosity <= 0:
            raise ValueError(f"Invalid luminosity: {context}")
          if not math.isfinite(sample.cross_section) or sample.cross_section < 0:
            raise ValueError(f"Invalid cross section: {context}")
          self.normalizer.normalize(member, sample)
        member.hist.Rebin2D(hist.x_rebin, hist.y_rebin)
        if combined is None:
          combined = member.hist
        elif not combined.Add(member.hist):
          raise ValueError(f"Could not add histogram: {context}")
      result.append((group, combined))
    return result

  @staticmethod
  def shared_limits(hist: Any, groups: list[tuple[HistogramGroup2D, Any]]) -> tuple[float, float]:
    values = [item.GetBinContent(x, y) for _, item in groups for x, y in displayed_bins(item)]
    if not values or not all(math.isfinite(value) for value in values):
      raise ValueError(f"Invalid displayed bin contents for '{hist.getName()}'")
    if hist.log_z:
      positive = [value for value in values if value > 0]
      if not positive:
        warn(f"Logarithmic grouped plot '{hist.getName()}' has no positive displayed bins; drawing an empty heatmap")
        minimum, maximum = 1.0, 10.0
      else:
        minimum, maximum = min(positive), max(positive)
        if minimum == maximum:
          minimum *= 0.5
          maximum *= 2.0
    else:
      minimum, maximum = min(0.0, min(values)), max(0.0, max(values))
      if minimum == maximum:
        maximum = minimum + 1.0
    minimum = hist.z_min if hist.z_min is not None else minimum
    maximum = hist.z_max if hist.z_max is not None else maximum
    if not math.isfinite(minimum) or not math.isfinite(maximum) or minimum >= maximum:
      raise ValueError(f"Invalid shared color limits for '{hist.getName()}'")
    if hist.log_z and minimum <= 0:
      raise ValueError(f"Logarithmic z-axis limits must be positive for '{hist.getName()}'")
    return minimum, maximum

  def palette_exec(self, colors: tuple[int, ...]) -> Any:
    # ROOT repaints in primitive order, so palette selection must be a drawable.
    command = (
      "[]{ static int colors[] = {"
      + ",".join(map(str, colors))
      + "}; gStyle->SetPalette("
      + str(len(colors))
      + ", colors); }();"
    )
    execution = ROOT.TExec(f"tea_palette_{next(_ids)}", command)
    execution.Draw()
    self.retained.append(execution)
    return execution

  def draw(self, hist: Any, objects: list[tuple[Any, Any]]) -> Any:
    groups = self.prepare_groups(hist, objects)
    saved_palette = tuple(ROOT.gStyle.GetColorPalette(index) for index in range(ROOT.gStyle.GetNumberOfColors()))
    try:
      return self._draw(hist, groups, saved_palette)
    finally:
      ROOT.gStyle.SetPalette(len(saved_palette), array("i", saved_palette))

  def _draw(self, hist: Any, groups: list[tuple[HistogramGroup2D, Any]], saved_palette: tuple[int, ...]) -> Any:
    size = getattr(self.config, "canvas_size_2Dhists", self.config.canvas_size)
    heatmaps = [(group, item) for group, item in groups if group.draw_heatmap]
    column_width = 160
    width = size[0] + column_width * len(heatmaps)
    name = hist.getOutputName() + "_grouped"
    canvas = ROOT.TCanvas(f"{name}_{next(_ids)}", hist.title, width, size[1])
    canvas.SetCanvasSize(width, size[1])
    plot = ROOT.TPad(f"tea_plot_{next(_ids)}", "", 0, 0, size[0] / width, 1)
    plot.SetNumber(1)
    plot.Draw()
    plot.cd()
    self.styler.setup_2d_pad(plot, square_frame=hist.comparable_axes, with_colorbar=False)
    plot.SetLogx(hist.log_x)
    plot.SetLogy(hist.log_y)
    plot.SetLogz(hist.log_z and bool(heatmaps))
    plot.SetGridx(getattr(self.config, "show_grid_2D", False))
    plot.SetGridy(getattr(self.config, "show_grid_2D", False))
    for group, item in groups:
      self.styler.setupFigure2D(item, hist)
      self.styler.getComparable2DAxisRange(item, hist)
      if not all(math.isfinite(item.GetBinContent(x, y)) for x, y in displayed_bins(item)):
        raise ValueError(f"Nonfinite displayed bin content: group '{group.name}', histogram '{hist.getName()}'")
    minimum, maximum = self.shared_limits(hist, heatmaps) if heatmaps else (0.0, 1.0)
    palettes = {}
    for group, item in groups:
      ROOT.gStyle.SetPalette(int(group.palette))
      opaque = tuple(ROOT.gStyle.GetColorPalette(index) for index in range(ROOT.gStyle.GetNumberOfColors()))
      transparent = tuple(ROOT.TColor.GetColorTransparent(color, group.alpha) for color in opaque)
      palettes[group.name] = (opaque, transparent)
      if group.draw_heatmap:
        item.SetMinimum(minimum)
        item.SetMaximum(maximum)
        item.SetContour(len(opaque))
    legend_config = getattr(self.config, "legend2D", Legend(0.16, 0.72, 0.46, 0.88, "f", fill_color=ROOT.kWhite))
    legend = legend_config.getRootLegend()
    frame = clone_histogram(groups[0][1], "frame")
    frame.Reset()
    frame.SetMinimum(minimum)
    frame.SetMaximum(maximum)
    frame.Draw("AXIS")
    self.retained.append(frame)
    for group, item in heatmaps:
      opaque, transparent = palettes[group.name]
      self.palette_exec(transparent)
      item.Draw("COL1 SAME")
      swatch = ROOT.TBox()
      swatch.SetFillColor(opaque[len(opaque) // 2] if group.palette == ROOT.kGreyScale else opaque[-1])
      swatch.SetFillStyle(1001)
      label = group.legend_description
      if not any(item.GetBinContent(x, y) > 0 for x, y in displayed_bins(item)):
        label += " (no positive displayed weight)"
      legend.AddEntry(swatch, label, "f")
      self.retained.extend((item, swatch))
    contours_enabled = (
      getattr(self.config, "show_contours_2D", False) if hist.show_contours is None else hist.show_contours
    )
    fractions = tuple(
      getattr(self.config, "contour_fractions_2D", (0.68, 0.95))
      if hist.contour_fractions is None
      else hist.contour_fractions
    )
    styles = {0.68: 1, 0.95: 2}
    for index, fraction in enumerate(value for value in fractions if value not in styles):
      styles[fraction] = index % 8 + 3
    drawn_fractions = set()
    for group, item in groups:
      enabled = contours_enabled if group.show_contours is None else group.show_contours
      if not enabled:
        continue
      opaque, _ = palettes[group.name]
      color = opaque[-1] if group.contour_color is None else group.contour_color
      context = f"group '{group.name}', histogram '{hist.getName()}'"
      density, regions = probability_regions(item, fractions, context)
      self.retained.append(density)
      if not group.draw_heatmap:
        swatch = ROOT.TLine()
        swatch.SetLineColor(color)
        swatch.SetLineWidth(2)
        label = group.legend_description if regions else group.legend_description + " (no positive displayed weight)"
        legend.AddEntry(swatch, label, "l")
        self.retained.append(swatch)
      for fraction, threshold, _ in regions:
        style = styles[fraction]
        values = [density.GetBinContent(x, y) for x, y in displayed_bins(density)]
        if min(values) >= threshold:
          xaxis, yaxis = density.GetXaxis(), density.GetYaxis()
          line = ROOT.TBox(
            xaxis.GetBinLowEdge(xaxis.GetFirst()),
            yaxis.GetBinLowEdge(yaxis.GetFirst()),
            xaxis.GetBinUpEdge(xaxis.GetLast()),
            yaxis.GetBinUpEdge(yaxis.GetLast()),
          )
          line.SetFillStyle(0)
          option = "same"
        else:
          line = clone_histogram(density, "contour")
          line.SetContour(1, array("d", [math.nextafter(threshold, -math.inf)]))
          option = "CONT3 SAME"
        line.SetLineColor(color)
        line.SetLineWidth(2)
        line.SetLineStyle(style)
        line.Draw(option)
        self.retained.append(line)
        drawn_fractions.add(fraction)
    for fraction in fractions:
      if fraction not in drawn_fractions:
        continue
      swatch = ROOT.TLine()
      swatch.SetLineColor(ROOT.kBlack)
      swatch.SetLineWidth(2)
      swatch.SetLineStyle(styles[fraction])
      legend.AddEntry(swatch, f"{fraction:.0%} region", "l")
      self.retained.append(swatch)
    comparable = self.styler.getComparable2DAxisRange(groups[0][1], hist)
    if comparable is not None and getattr(self.config, "show_y_equals_x_2D", False):
      diagonal = ROOT.TLine(comparable[0], comparable[0], comparable[1], comparable[1])
      diagonal.Draw("same")
      self.retained.append(diagonal)
    plot.RedrawAxis()
    legend.Draw()
    self.retained.extend((plot, legend))
    self.palette_exec(saved_palette)
    for index, (group, item) in enumerate(heatmaps):
      opaque, _ = palettes[group.name]
      canvas.cd()
      bar_pad = ROOT.TPad(
        f"tea_bar_{next(_ids)}",
        "",
        (size[0] + index * column_width) / width,
        0,
        (size[0] + (index + 1) * column_width) / width,
        1,
      )
      bar_pad.Draw()
      bar_pad.cd()
      bar_pad.SetLogz(hist.log_z)
      self.palette_exec(opaque)
      bar_hist = clone_histogram(item, "colorbar")
      bar_hist.GetZaxis().SetLabelSize(self.styler.labelFontSize / column_width)
      bar_hist.GetZaxis().SetTitleSize(self.styler.labelFontSize / column_width)
      palette = ROOT.TPaletteAxis(0.08, plot.GetBottomMargin(), 0.25, 1 - plot.GetTopMargin(), bar_hist)
      palette.Draw()
      caption = ROOT.TLatex(0.06, 0.97, group.legend_description)
      caption.SetNDC()
      caption.SetTextFont(42)
      caption.SetTextSize(20 / column_width)
      caption.Draw()
      self.retained.extend((bar_pad, bar_hist, palette, caption))
      self.palette_exec(saved_palette)
    canvas.cd()
    canvas.Modified()
    canvas.Update()
    self.canvases.append(canvas)
    return canvas
