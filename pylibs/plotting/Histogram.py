from dataclasses import dataclass
from copy import deepcopy
from array import array
import ROOT

from Sample import SampleType
from HistogramNormalizer import NormalizationType
from Logger import info, warn, error


@dataclass
class Histogram:
  name: str = ""
  title: str = ""
  log_x: bool = False
  log_y: bool = False
  norm_type: int = NormalizationType.to_lumi
  rebin: int = 1
  x_min: float = 0.0
  x_max: float = 0.0
  y_min: float = 0.0
  y_max: float = 0.0
  x_label: str = ""
  y_label: str = ""
  suffix: str = ""
  error: float = -1.0
  entries: int = 0

  def __post_init__(self):
    self.hist = None
    self.rand = ROOT.TRandom3()
    self.rand.SetSeed(0)

  def set_hist(self, hist):
    self.hist = hist

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
    if self.hist.GetEntries() == 0:
      self.hist.Fill(0.0, 1e-99)

    if not self.isGood():
      return

    if self.x_max > 0 or self.x_min > 0:
      original_bins = [self.hist.GetBinLowEdge(i) for i in range(1, self.hist.GetNbinsX() + 2)]
      new_bin_edges = [x for x in original_bins if self.x_min <= x <= self.x_max]
      if self.x_max not in new_bin_edges:
        new_bin_edges.append(self.x_max)

      new_n_bins = len(new_bin_edges) - 1
      new_histogram = ROOT.TH1F(f"{self.hist.GetName()}_{self.rand.Integer(1000000)}",
                                self.hist.GetTitle(), new_n_bins, array('d', new_bin_edges))

      for i in range(1, new_n_bins + 1):
        original_bin = self.hist.FindBin(new_bin_edges[i-1])
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
    self.hist.Rebin(self.rebin)
    self.hist.Scale(1./self.rebin)
    self.hist.SetBinErrorOption(ROOT.TH1.kPoisson)

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
  x_min: float = 0.0
  x_max: float = 0.0
  y_min: float = 0.0
  y_max: float = 0.0
  z_min: float = 0.0
  z_max: float = 0.0
  x_label: str = ""
  y_label: str = ""
  z_label: str = ""
  suffix: str = ""

  def set_hist(self, hist):
    self.hist = hist

  def load(self, input_file):
    self.hist = deepcopy(input_file.Get(self.name))

    if self.hist is None or type(self.hist) is ROOT.TObject:
      error(f"Could not find histogram: {self.name} in file {input_file.GetName()}")
      return

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
