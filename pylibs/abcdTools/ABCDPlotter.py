"""Config-driven ABCD loading, common cut search, and PDF diagnostics."""

from __future__ import annotations

from array import array
from ctypes import c_double
import json
import hashlib
import subprocess
import math
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import ROOT

from ABCDSearch import DIRECTIONS, IntegralPlane, boundary_indices, metrics, region_table, regions, search
from ABCDHelper import ABCDHelper
from Sample import SampleType


DEFAULTS = dict(
  max_correlation=None,
  max_overlap=None,
  max_closure=0.2,
  max_error=2.0,
  min_n_events=20.0,
  max_signal_contamination=0.2,
  min_signals=1,
  overlap_metric="cosine",
)


def edges(axis: Any) -> list[float]:
  return [axis.GetBinLowEdge(i) for i in range(1, axis.GetNbins() + 2)]


def evaluate_planes(planes: dict, point: tuple[int, int], quadrant: str) -> dict:
  helper = ABCDHelper()
  output = {}
  for region, histograms in planes.items():
    b = regions(helper, IntegralPlane(histograms["background"]), point, quadrant)
    output[region] = {"background": region_table(*b)}
    for key, h in histograms.items():
      if key == "background":
        continue
      s = regions(helper, IntegralPlane(h), point, quadrant)
      output[region][key] = {"metrics": metrics(helper, b, s), "regions": region_table(*s)}
  return output


class ABCDPlotter:
  def __init__(self, config: Any, args: Any = None) -> None:
    self.config = config
    self.settings = {}
    for key, default in DEFAULTS.items():
      override = getattr(args, key, None)
      self.settings[key] = override if override is not None else getattr(config, key, default)
    for key, value in self.settings.items():
      if key != "overlap_metric" and value is not None and (not math.isfinite(value) or value < 0):
        raise ValueError(f"Invalid constraint: {key}")
    if not hasattr(config, "signal_models"):
      raise ValueError(
        "Migrate ABCD config: supply signal_models with label, parameters and Sample objects; "
        "ttalps path patterns and masses/ctaus are no longer input interfaces"
      )
    self.models = config.signal_models
    if not self.models or any(not re.fullmatch(r"[A-Za-z0-9_.-]+", key) for key in self.models):
      raise ValueError("Signal model IDs must be nonempty filename-safe strings")
    self.selected = list(getattr(config, "optimization_signals", self.models))
    self.normalization = []
    self.planes = self._load()
    self.result = None
    self.maps = None

  @classmethod
  def from_histograms(
    cls,
    config: Any,
    planes: dict,
    models: dict,
    selected: list[str],
    result: dict,
    maps: dict,
    normalization: list[dict] | None = None,
  ) -> ABCDPlotter:
    """Prepared inputs are already normalized and rebinned; never scale them again."""
    instance = cls.__new__(cls)
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]+", key) for key in models):
      raise ValueError("Signal model IDs must be filename-safe strings")
    instance.config, instance.planes, instance.models = config, planes, models
    instance.selected, instance.result, instance.maps = selected, result, maps
    instance.normalization = normalization or []
    return instance

  def _load(self) -> dict:
    config = self.config
    factor = getattr(config, "rebin_2D", 1)
    if not isinstance(factor, int) or factor < 1:
      raise ValueError("rebin_2D must be a positive integer")
    region = getattr(config, "region", "SR")
    suffix = getattr(config, "category", "")
    pair = f"{config.variable_1}_vs_{config.variable_2}"
    bg_name = getattr(config, "background_hist_name", f"{config.background_collection}_{pair}{suffix}")
    sig_name = getattr(config, "signal_hist_name", f"{config.signal_collection}_{pair}{suffix}")
    background_samples = (
      getattr(config, "data_samples", ()) if getattr(config, "do_data", False) else config.background_samples
    )
    groups = {"background": (background_samples, bg_name)}
    groups.update({key: (model["samples"], sig_name) for key, model in self.models.items()})
    if "background" in self.models:
      raise ValueError("Signal model ID 'background' is reserved")
    output, reference_edges, seen = {}, None, set()
    for key, (samples, name) in groups.items():
      if not samples:
        raise ValueError(f"No configured samples for {key}")
      for sample in samples:
        identity = (sample.file_path, name)
        if identity in seen:
          raise ValueError(f"Duplicate sample input: {identity}")
        seen.add(identity)
        file = ROOT.TFile.Open(sample.file_path)
        if not file or file.IsZombie() or file.TestBit(ROOT.TFile.kRecovered):
          raise ValueError(f"Unreadable ROOT input: {sample.file_path}")
        try:
          original = file.Get(name)
          if not original or not original.InheritsFrom("TH2"):
            raise ValueError(f"Missing TH2 {name}: {sample.file_path}")
          if not original.GetSumw2N():
            raise ValueError(f"Missing stored squared weights: {sample.file_path}:{name}")
          current_edges = (edges(original.GetXaxis()), edges(original.GetYaxis()))
          if reference_edges is not None and current_edges != reference_edges:
            raise ValueError("Incompatible ABCD histogram axes")
          reference_edges = current_edges
          if any(n % factor or n // factor < 2 for n in (original.GetNbinsX(), original.GetNbinsY())):
            raise ValueError("Rebinning must exactly merge axes and retain interior boundaries")
          h = original.Clone(uuid4().hex)
          h.SetDirectory(0)
          scale, initial, lumi = 1.0, None, None
          if sample.type != SampleType.data:
            cutflow = file.Get("cutFlow")
            if not cutflow:
              raise ValueError(f"Missing cutFlow: {sample.file_path}")
            initial = sample.initial_weight_sum if sample.initial_weight_sum > 0 else cutflow.GetBinContent(1)
            lumi = sample.luminosity if sample.luminosity > 0 else getattr(config, "luminosity", None)
            if any(v is None or not math.isfinite(v) or v <= 0 for v in (initial, lumi, sample.cross_section)):
              raise ValueError(f"Invalid normalization: {sample.name}")
            scale = lumi * sample.cross_section / initial
            h.Scale(scale)
          self.normalization.append(
            dict(
              model=key,
              sample=sample.name,
              path=sample.file_path,
              luminosity_pb=lumi,
              cross_section_pb=sample.cross_section,
              initial_generator_weight_sum=initial,
              scale=scale,
            )
          )
          h.Rebin2D(factor, factor)
          if key in output:
            output[key].Add(h)
          else:
            output[key] = h
        finally:
          file.Close()
    return {region: output}

  def calculate_best_points(self) -> dict:
    region = getattr(self.config, "region", "SR")
    histograms = self.planes[region]
    if getattr(self.config, "optimization_param", "significance") not in (None, "significance"):
      raise ValueError("Use significance optimization or explicit fixed-point mode")
    fixed = (
      getattr(self.config, "abcd_point", None)
      if getattr(self.config, "optimization_param", "significance") is None
      else None
    )
    if getattr(self.config, "optimization_param", "significance") is None and not isinstance(fixed, dict):
      raise ValueError("Fixed-point mode requires physical abcd_point x/y boundaries")
    order = (self.config.signal_bin,) if fixed else ("A", "B", "C", "D")
    self.result, self.maps = search(
      histograms["background"],
      {key: h for key, h in histograms.items() if key != "background"},
      self.selected,
      self.settings,
      fixed,
      order,
    )
    self.result.update(
      settings=self.settings,
      normalization=self.normalization,
      region=region,
      pair=f"{self.config.variable_1}_vs_{self.config.variable_2}",
      model_metadata={key: {k: v for k, v in model.items() if k != "samples"} for key, model in self.models.items()},
    )
    if self.result["status"] == "accepted":
      self.result["evaluations"] = evaluate_planes(self.planes, tuple(self.result["indices"]), self.result["quadrant"])
    source = Path(__file__).resolve()
    framework = source.parents[2]
    try:
      revision = subprocess.check_output(["git", "-C", str(framework), "rev-parse", "HEAD"], text=True).strip()
      dirty = subprocess.check_output(["git", "-C", str(framework), "status", "--short"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
      revision, dirty = None, None
    self.result["provenance"] = {
      "tea_commit": revision,
      "working_tree": dirty,
      "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.parent.glob("ABCD*.py")},
    }
    self.result["counting_convention"] = getattr(
      self.config, "counting_convention", "Producer-defined entries; inter-entry event covariance is omitted"
    )
    return self.result

  def _label(self, key: str) -> str:
    return self.models.get(key, {}).get("label", key)

  def _canvas(self, columns: int = 1, rows: int = 1) -> Any:
    size = getattr(self.config, "canvas_size", (900, 750))
    width, height = (size, size) if isinstance(size, int) else size
    canvas = ROOT.TCanvas(uuid4().hex, "", min(width * columns, 2400), min(height * rows, 2400))
    if columns * rows > 1:
      canvas.Divide(columns, rows)
    canvas.cd()
    return canvas

  def _style(self) -> None:
    ROOT.gPad.SetLeftMargin(0.14)
    ROOT.gPad.SetRightMargin(0.15)
    ROOT.gPad.SetBottomMargin(0.16)

  def _axes(self, hist: Any) -> None:
    labels = getattr(self.config, "nice_names", {})
    hist.GetXaxis().SetTitle(labels.get(self.config.variable_2, self.config.variable_2))
    hist.GetYaxis().SetTitle(labels.get(self.config.variable_1, self.config.variable_1))
    for axis in (hist.GetXaxis(), hist.GetYaxis()):
      axis.SetTitleSize(0.035)
      axis.SetTitleOffset(1.35)

  def _lines(self, hist: Any) -> list:
    if self.result["status"] != "accepted":
      return []
    point = self.result["physical_boundaries"]
    lines = [
      ROOT.TLine(point["x"], hist.GetYaxis().GetXmin(), point["x"], hist.GetYaxis().GetXmax()),
      ROOT.TLine(hist.GetXaxis().GetXmin(), point["y"], hist.GetXaxis().GetXmax(), point["y"]),
    ]
    for line in lines:
      line.SetLineWidth(2)
      line.Draw()
    return lines

  def render(self) -> None:
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    if self.result is None:
      self.calculate_best_points()
    output = Path(self.config.output_path)
    output.mkdir(parents=True, exist_ok=True)
    if tuple(getattr(self.config, "output_formats", ("pdf",))) != ("pdf",):
      raise ValueError("ABCD diagnostics support PDF output only")
    kept = []
    for region, histograms in self.planes.items():
      for start in range(0, len(histograms), 12):
        entries = list(histograms.items())[start : start + 12]
        columns = min(3, len(entries))
        canvas = self._canvas(columns, math.ceil(len(entries) / columns))
        for pad, (key, original) in enumerate(entries, 1):
          canvas.cd(pad)
          self._style()
          h = original.Clone(uuid4().hex)
          h.SetDirectory(0)
          h.SetTitle(f"{region}: {self._label(key)}")
          self._axes(h)
          h.Draw("COLZ")
          kept.extend([h, *self._lines(h)])
        canvas.SaveAs(str(output / f"{region}_planes_{start // 12 + 1}.pdf"))
        canvas.Close()
    self._signal_grids(output, kept)
    for name in ("significance", "closure", "error", "leakage", "min_n_events", "accepted"):
      self._draw_maps(name, output, kept)
    for key in self.selected:
      for name in ("significance", "leakage"):
        self._draw_maps(f"{name}:{key}", output, kept)
    if self.result["status"] == "accepted":
      for region in self.planes:
        self._projections(region, output, kept)
      self._summary(output, kept)

  def _signal_grids(self, output: Path, kept: list) -> None:
    for region, histograms in self.planes.items():
      models = [(key, histograms[key]) for key in self.models if key in histograms]
      for start in range(0, len(models), 12):
        entries = models[start : start + 12]
        columns = min(3, len(entries))
        canvas = self._canvas(columns, math.ceil(len(entries) / columns))
        for pad, (key, original) in enumerate(entries, 1):
          canvas.cd(pad)
          self._style()
          background = histograms["background"].Clone(uuid4().hex)
          signal = original.Clone(uuid4().hex)
          for h in (background, signal):
            h.SetDirectory(0)
            if h.Integral() > 0:
              h.Scale(1.0 / h.Integral())
          background.SetMinimum(0.0)
          signal.SetMinimum(0.0)
          background.SetTitle(f"{region}: {self._label(key)} (unit-area shapes)")
          self._axes(background)
          background.SetFillColor(ROOT.kGray + 1)
          background.SetLineColor(ROOT.kGray + 1)
          signal.SetFillColor(ROOT.kRed)
          signal.SetLineColor(ROOT.kRed)
          background.Draw("BOX")
          signal.Draw("BOX SAME")
          legend = ROOT.TLegend(0.15, 0.80, 0.75, 0.89)
          legend.SetTextSize(0.025)
          legend.AddEntry(background, "Background", "f")
          legend.AddEntry(signal, "Signal", "f")
          legend.Draw()
          kept.extend([background, signal, legend, *self._lines(background)])
        canvas.SaveAs(str(output / f"{region}_signal_grid_{start // 12 + 1}.pdf"))
        canvas.Close()

  def _draw_maps(self, name: str, output: Path, kept: list) -> None:
    background = next(iter(self.planes.values()))["background"]
    canvas = self._canvas(2, 2)
    for pad, (quadrant, fields) in enumerate(self.maps.items(), 1):
      canvas.cd(pad)
      self._style()
      x, y = np.array(edges(background.GetXaxis())[1:-1]), np.array(edges(background.GetYaxis())[1:-1])

      def map_edges(values: np.ndarray, axis: Any) -> array:
        if len(values) == 1:
          half = axis.GetBinWidth(1) / 2
          return array("d", [values[0] - half, values[0] + half])
        middle = (values[:-1] + values[1:]) / 2
        return array("d", [values[0] - (middle[0] - values[0]), *middle, values[-1] + (values[-1] - middle[-1])])

      h = ROOT.TH2D(
        uuid4().hex,
        f"{name}, quadrant {quadrant}",
        len(x),
        map_edges(x, background.GetXaxis()),
        len(y),
        map_edges(y, background.GetYaxis()),
      )
      h.SetDirectory(0)
      self._axes(h)
      h.GetXaxis().SetTitle(h.GetXaxis().GetTitle() + " boundary")
      h.GetYaxis().SetTitle(h.GetYaxis().GetTitle() + " boundary")
      for (i, j), value in np.ndenumerate(fields[name]):
        h.SetBinContent(i + 1, j + 1, float(value) if np.isfinite(value) else 0.0)
      h.Draw("COLZ")
      params = getattr(self.config, "z_params", {}).get(name.split(":")[0])
      if params:
        h.GetZaxis().SetTitle(params[0])
        h.GetZaxis().SetRangeUser(params[1], params[2])
        ROOT.gPad.SetLogz(params[3])
      kept.append(h)
      note = ROOT.TLatex()
      note.SetTextSize(0.027)
      note.DrawLatexNDC(0.15, 0.93, "Undefined bins shown as zero; see numeric maps")
      kept.extend([note, *self._lines(h)])
    canvas.SaveAs(str(output / (name.replace(":", "_") + ".pdf")))
    canvas.Close()

  def projections(self, region: str) -> dict:
    """Aggregate before propagating the shared control normalization uncertainty."""
    hist = self.planes[region]["background"]
    point, q = tuple(self.result["indices"]), self.result["quadrant"]
    i, j = point
    nx, ny = hist.GetNbinsX(), hist.GetNbinsY()
    low_x, high_y = DIRECTIONS[q][0] == "<", DIRECTIONS[q][1] == ">="
    sx, cx = ((1, i - 1), (i, nx)) if low_x else ((i, nx), (1, i - 1))
    sy, cy = ((j, ny), (1, j - 1)) if high_y else ((1, j - 1), (j, ny))
    b, be = regions(ABCDHelper(), hist, point, q)
    if any(v <= 0 for v in b):
      return {"available": False, "reason": "Nonpositive background region yield"}
    ratio = b[1] / b[3]
    variance = ratio**2 * ((be[1] / b[1]) ** 2 + (be[3] / b[3]) ** 2)
    base_edges = edges(hist.GetYaxis())[sy[0] - 1 : sy[1] + 1]
    custom = getattr(self.config, "custom_rebin", False)
    smart = getattr(self.config, "smart_rebin", False)
    if custom and smart:
      raise ValueError("Choose either custom or smart projection rebinning")
    if custom:
      boundaries = list(self.config.custom_projections_binning)
      if boundaries[0] != base_edges[0] or boundaries[-1] != base_edges[-1]:
        raise ValueError("Custom projection bins must span the selected signal side")
    elif smart:
      boundaries, total, squares = [base_edges[0]], 0.0, 0.0
      for ybin in range(sy[0], sy[1] + 1):
        err = c_double()
        total += hist.IntegralAndError(*sx, ybin, ybin, err)
        squares += err.value**2
        if total > 0 and math.sqrt(squares) / total <= self.config.smart_rebin_max_error:
          boundaries.append(hist.GetYaxis().GetBinUpEdge(ybin))
          total, squares = 0.0, 0.0
      if boundaries[-1] != base_edges[-1]:
        if len(boundaries) > 1:
          boundaries.pop()
        boundaries.append(base_edges[-1])
    else:
      factor = getattr(self.config, "standard_rebin", 1)
      if not isinstance(factor, int) or factor < 1 or (len(base_edges) - 1) % factor:
        raise ValueError("Projection rebinning must exactly merge the selected range")
      boundaries = base_edges[::factor]
    if any(value not in base_edges for value in boundaries) or any(a >= b for a, b in zip(boundaries, boundaries[1:])):
      raise ValueError("Projection boundaries must coincide with ordered base edges")
    true, predicted, controls, signals = [], [], [], {key: [] for key in self.models if key in self.planes[region]}
    for left, right in zip(boundaries, boundaries[1:]):
      first = base_edges.index(left) + sy[0]
      last = base_edges.index(right) + sy[0] - 1

      def integral(h: Any, xbins: tuple[int, int]) -> tuple[float, float]:
        error = c_double()
        return h.IntegralAndError(*xbins, first, last, error), error.value**2

      a, va = integral(hist, sx)
      c, vc = integral(hist, cx)
      true.append((a, math.sqrt(va)))
      predicted.append((ratio * c, math.sqrt(ratio**2 * vc + c**2 * variance)))
      controls.append(c)
      for key in signals:
        s, vs = integral(self.planes[region][key], sx)
        signals[key].append((s, math.sqrt(vs)))
    covariance = np.outer(controls, controls) * variance
    for k, (_, error) in enumerate(predicted):
      covariance[k, k] = error**2
    return dict(
      available=True,
      edges=boundaries,
      true=true,
      prediction=predicted,
      signals=signals,
      prediction_covariance=covariance.tolist(),
    )

  def _projections(self, region: str, output: Path, kept: list) -> None:
    data = self.projections(region)
    (output / f"{region}_projections.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    if not data["available"]:
      return

    def histogram(label: str, values: list, color: int) -> Any:
      h = ROOT.TH1D(uuid4().hex, label, len(data["edges"]) - 1, array("d", data["edges"]))
      h.SetDirectory(0)
      h.Sumw2()
      for index, (value, error) in enumerate(values, 1):
        h.SetBinContent(index, value)
        h.SetBinError(index, error)
      h.SetLineColor(color)
      h.SetMarkerColor(color)
      kept.append(h)
      return h

    models = list(data["signals"].items())
    for page, start in enumerate(range(0, len(models), 8)):
      entries = models[start : start + 8]
      canvas = self._canvas()
      top = ROOT.TPad(uuid4().hex, "", 0.0, 0.30, 1.0, 1.0)
      bottom = ROOT.TPad(uuid4().hex, "", 0.0, 0.0, 1.0, 0.30)
      top.Draw()
      bottom.Draw()
      top.cd()
      top.SetLeftMargin(0.14)
      top.SetRightMargin(0.32)
      top.SetBottomMargin(0.02)
      lumi = getattr(self.config, "luminosity", None)
      title = f"{region}: background prediction and simulation"
      if lumi is not None:
        title += f", {lumi / 1000:g} fb^{{-1}}"
      true = histogram(title, data["true"], ROOT.kBlack)
      pred = histogram("", data["prediction"], ROOT.kRed + 1)
      legend = ROOT.TLegend(0.70, 0.50, 0.99, 0.90)
      legend.SetTextSize(0.028)
      legend.AddEntry(true, "Background simulation", "lep")
      legend.AddEntry(pred, "ABCD prediction", "lep")
      curves = []
      for index, (key, values) in enumerate(entries):
        color = self.models[key].get("color", ROOT.kBlue + index % 5)
        curve = histogram("", values, color)
        display_scale = getattr(self.config, "signal_display_scale", 1.0)
        curve.Scale(display_scale)
        suffix = f" (x{display_scale:g})" if display_scale != 1 else ""
        legend.AddEntry(curve, self._label(key) + suffix, "l")
        curves.append(curve)
      true.SetMaximum(max(h.GetMaximum() for h in [true, pred, *curves]) * 1.35)
      true.SetMinimum(min(0.0, *(h.GetMinimum() for h in [true, pred, *curves])))
      true.GetYaxis().SetTitle("Events")
      true.GetXaxis().SetLabelSize(0.0)
      true.GetYaxis().SetTitleSize(0.05)
      true.Draw("E")
      pred.Draw("E SAME")
      for curve in curves:
        curve.Draw("HIST SAME")
      legend.Draw()
      bottom.cd()
      bottom.SetLeftMargin(0.14)
      bottom.SetRightMargin(0.32)
      bottom.SetTopMargin(0.03)
      bottom.SetBottomMargin(0.35)
      frame = true.Clone(uuid4().hex)
      frame.Reset()
      frame.SetTitle("")
      frame.SetMinimum(0.0)
      frame.SetMaximum(getattr(self.config, "y_max_ratio", 2.0))
      frame.GetYaxis().SetTitle("Prediction / simulation")
      frame.GetYaxis().SetTitleSize(0.08)
      frame.GetYaxis().SetTitleOffset(0.75)
      frame.GetYaxis().SetLabelSize(0.08)
      frame.GetYaxis().SetNdivisions(505)
      frame.GetXaxis().SetTitle(
        getattr(self.config, "nice_names", {}).get(self.config.variable_1, self.config.variable_1)
      )
      frame.GetXaxis().SetTitleSize(0.10)
      frame.GetXaxis().SetLabelSize(0.09)
      frame.Draw("AXIS")
      graph = ROOT.TGraphErrors()
      for k, ((p, ep), (a, ea)) in enumerate(zip(data["prediction"], data["true"])):
        if a <= 0:
          continue
        n = graph.GetN()
        graph.SetPoint(n, (data["edges"][k] + data["edges"][k + 1]) / 2, p / a)
        graph.SetPointError(n, 0.0, math.hypot(ep / a, p * ea / a**2))
      graph.SetTitle(
        f";{getattr(self.config, 'nice_names', {}).get(self.config.variable_1, self.config.variable_1)};Prediction / simulation"
      )
      graph.SetMarkerStyle(20)
      graph.Draw("P SAME")
      canvas.SaveAs(str(output / f"{region}_projections_ratio_{page + 1}.pdf"))
      kept.extend([legend, graph, frame, top, bottom])
      canvas.Close()

  def _summary(self, output: Path, kept: list) -> None:
    values = self.result.get("individual_significances", {})
    canvas = self._canvas()
    h = ROOT.TH1D(uuid4().hex, "", len(self.selected), 0.0, len(self.selected))
    h.SetDirectory(0)
    for i, key in enumerate(self.selected, 1):
      h.SetBinContent(i, values[key])
      h.GetXaxis().SetBinLabel(i, self._label(key))
    h.LabelsOption("v")
    h.GetYaxis().SetTitle("S / sqrt(S + B)")
    ROOT.gPad.SetBottomMargin(0.35)
    ROOT.gPad.SetTopMargin(0.15)
    h.Draw("HIST")
    label = ROOT.TLatex()
    label.SetTextSize(0.03)
    label.DrawLatexNDC(0.12, 0.95, "Individual significance at common cuts")
    point = self.result["physical_boundaries"]
    label.DrawLatexNDC(
      0.12,
      0.89,
      f"Quadrant {self.result['quadrant']}, x={point['x']:g}, y={point['y']:g}; sum={sum(values.values()):.4g}",
    )
    canvas.SaveAs(str(output / "model_summary.pdf"))
    kept.extend([h, label])
