from dataclasses import dataclass
from copy import deepcopy
from array import array
from itertools import count
from typing import Callable, Optional, Union
from math import isclose, isfinite
from bisect import bisect_left
import ROOT

from Sample import SampleType
from HistogramNormalizer import NormalizationType
from Logger import info, warn, error


_cropped_histogram_ids = count()


@dataclass
class Histogram:
  name: str = ""
  title: str = ""
  log_x: bool = False
  log_y: bool = False
  norm_type: int = NormalizationType.to_lumi
  rebin: int = 1
  x_min: Optional[float] = None
  x_max: Optional[float] = None
  y_min: Optional[float] = None
  y_max: Optional[float] = None
  x_label: str = ""
  y_label: str = ""
  suffix: str = ""
  error: float = -1.0
  entries: int = 0
  scale_bin: bool = False
  scale_by_bin_width: bool = False
  # Keep the configured data crop, but permit display whitespace for a legend.
  allow_legend_x_extension: bool = False
  # Keys are stored category/status values, including negative failure codes.
  bin_labels: Optional[dict[int, str]] = None
  bin_edges: Optional[Union[tuple[float, ...], Callable]] = None
  # Display the booked domain without manufacturing bins from overflow.
  show_full_x_range: bool = False

  def __post_init__(self):
    self.hist = None

  def set_hist(self, hist):
    self.hist = hist

  def set_hist_name(self, name):
    self.hist.SetName(name)
    self.name = name

  def getName(self):
    return self.name + self.suffix

  def print(self):
    info(f"Histogram {self.name}, {self.hist}")

  def load(self, input_file):
    self.hist = input_file.Get(self.name)

    if self.hist is None:
      warn(f"Could not find histogram: {self.name}")
      return

    if not self.hist or type(self.hist) is ROOT.TObject:
      warn("Some histograms are invalid.")
      return

    self.entries = self.hist.GetEntries()
    if not self.isGood():
      return

    if self.x_min is not None or self.x_max is not None:
      original_bins = [self.hist.GetBinLowEdge(i) for i in range(1, self.hist.GetNbinsX() + 2)]
      x_min = self.x_min if self.x_min is not None else original_bins[0]
      x_max = self.x_max if self.x_max is not None else original_bins[-1]
      new_bin_edges = [x for x in original_bins if x_min <= x <= x_max]
      if x_max not in new_bin_edges:
        new_bin_edges.append(x_max)

      new_n_bins = len(new_bin_edges) - 1
      new_histogram = ROOT.TH1F(
        f"{self.hist.GetName()}_{next(_cropped_histogram_ids)}",
        self.hist.GetTitle(),
        new_n_bins,
        array("d", new_bin_edges),
      )

      for i in range(1, new_n_bins + 1):
        original_bin = self.hist.FindBin(new_bin_edges[i - 1])
        new_histogram.SetBinContent(i, self.hist.GetBinContent(original_bin))
        new_histogram.SetBinError(i, self.hist.GetBinError(original_bin))
        original_label = self.hist.GetXaxis().GetBinLabel(original_bin)
        if original_label != "":
          new_histogram.GetXaxis().SetBinLabel(i, original_label)
      self.hist = new_histogram

  def isGood(self):
    if self.hist is None:
      warn(f"Could not find histogram: {self.name}")
      return
    if not self.hist or type(self.hist) is ROOT.TObject:
      warn("Some histograms are invalid.")
      return
    if self.hist.GetEntries() == 0:
      return False

    return True

  def setup(self, sample):
    self.hist.SetLineStyle(sample.line_style)
    self.hist.SetLineColor(sample.line_color)
    self.hist.SetLineWidth(sample.line_width)
    self.hist.SetMarkerStyle(sample.marker_style)
    self.hist.SetMarkerSize(sample.marker_size)
    self.hist.SetMarkerColor(sample.marker_color)
    self.hist.SetLineColorAlpha(sample.line_color, sample.line_alpha)
    self.hist.SetFillColorAlpha(sample.fill_color, sample.fill_alpha)
    self.hist.SetFillStyle(sample.fill_style)
    if self.bin_edges is None:
      self.hist.Rebin(self.rebin)
    else:
      if self.rebin != 1:
        raise ValueError(f"{self.name}: choose either integer or variable rebinning")
      edges = tuple(self.bin_edges(self.hist) if callable(self.bin_edges) else self.bin_edges)
      source_edges = tuple(self.hist.GetBinLowEdge(i) for i in range(1, self.hist.GetNbinsX() + 2))
      aligned = lambda a, b: isclose(a, b, rel_tol=1.e-10, abs_tol=1.e-8)
      def is_source_edge(edge):
        index = bisect_left(source_edges, edge)
        return any(aligned(edge, source_edges[i]) for i in (index - 1, index) if 0 <= i < len(source_edges))
      if (len(edges) < 2 or not all(isfinite(edge) for edge in edges)
          or any(a >= b for a, b in zip(edges, edges[1:]))
          or not aligned(edges[0], source_edges[0])
          or not aligned(edges[-1], source_edges[-1])
          or any(not is_source_edge(edge) for edge in edges)):
        raise ValueError(f"{self.name}: variable bins must use existing edges and retain the full range")
      self.hist = self.hist.Rebin(len(edges) - 1, f"{self.hist.GetName()}_rebin_{next(_cropped_histogram_ids)}", array("d", edges))
      self.hist.SetDirectory(0)
    if self.bin_labels:
      axis = self.hist.GetXaxis()
      for value, label in self.bin_labels.items():
        index = axis.FindFixBin(value)
        if 1 <= index <= self.hist.GetNbinsX():
          axis.SetBinLabel(index, label)
    self.hist.SetBinErrorOption(ROOT.TH1.kPoisson)
    if self.scale_bin:
      self.hist.Scale(1.0 / self.rebin)
    if self.scale_by_bin_width:
      self.hist.Scale(1.0, "width")

  def setupRatio(self, sample):
    if sample.type == SampleType.background:
      color = sample.fill_color
    else:
      color = sample.line_color
    self.hist.SetLineColor(color)
    self.hist.SetMarkerColor(color)


@dataclass
class Histogram2D:
  name: str = ""
  title: str = ""
  log_x: bool = False
  log_y: bool = False
  log_z: bool = False
  norm_type: int = NormalizationType.to_lumi
  x_rebin: int = 1
  y_rebin: int = 1
  x_min: Optional[float] = None
  x_max: Optional[float] = None
  y_min: Optional[float] = None
  y_max: Optional[float] = None
  z_min: Optional[float] = None
  z_max: Optional[float] = None
  x_label: str = ""
  y_label: str = ""
  z_label: str = ""
  suffix: str = ""
  norm_scale: float = 1.0

  def __post_init__(self):
    self.hist = None

  def set_hist(self, hist):
    self.hist = hist

  def load(self, input_file):
    self.hist = deepcopy(input_file.Get(self.name))

    if self.hist is None or type(self.hist) is ROOT.TObject:
      error(f"Could not find histogram: {self.name} in file {input_file.GetName()}")
      return

    self.entries = self.hist.GetEntries()

  def set_hist_name(self, name):
    self.hist.SetName(name)
    self.name = name

  def isGood(self):
    if self.hist is None or type(self.hist) is ROOT.TObject:
      warn(f"Could not find histogram: {self.name}")
      return False
    if self.hist.GetEntries() == 0:
      warn(f"Histogram is empty: {self.name}")
      return False

    return True

  def setup(self, sample=None):
    if self.hist is None or type(self.hist) is ROOT.TObject:
      error(f"Could not find histogram: {self.name}")
      return

    self.hist.Rebin2D(self.x_rebin, self.y_rebin)

  def getName(self):
    return self.name + self.suffix
