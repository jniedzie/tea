from Logger import info, warn, error, fatal

from dataclasses import dataclass
from ROOT import TObject
from Sample import SampleType
from HistogramNormalizer import NormalizationType
import ROOT

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
  
  def __post_init__(self):
    self.hist = None
  
  def getName(self):
    return self.name + self.suffix
  
  def print(self):
    info(f"Histogram {self.name}, {self.hist}")
  
  def load(self, input_file):
    self.hist = input_file.Get(self.name)
    
    if self.hist is None or type(self.hist) is TObject:
      warn(f"Could not find histogram: {self.name}")
      return
    
    if self.hist.GetEntries() == 0:
      self.hist.Fill(0.0, 1e-99)
    
    if not self.isGood():
      return
    
    if self.x_max > 0:
      original_bins = [self.hist.GetBinLowEdge(i) for i in range(1, self.hist.GetNbinsX() + 2)]
      new_n_bins = len([x for x in original_bins if x < self.x_max])
      x_min = original_bins[0]
      new_histogram = ROOT.TH1F(self.hist.GetName(), self.hist.GetTitle(), new_n_bins, x_min, self.x_max)
      
      # fill the histogram:
      for i in range(1, new_n_bins + 1):
        new_histogram.SetBinContent(i, self.hist.GetBinContent(i))
        new_histogram.SetBinError(i, self.hist.GetBinError(i))
        # check if original histogram had custom labels on the x-axis:
        if self.hist.GetXaxis().GetBinLabel(i) != "":
          new_histogram.GetXaxis().SetBinLabel(i, self.hist.GetXaxis().GetBinLabel(i))
        
      self.hist = new_histogram
    
  def isGood(self):
    if self.hist is None or type(self.hist) is TObject:
      warn(f"Could not find histogram: {self.name}")
      return False
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
  
  def load(self, input_file):
    self.hist = input_file.Get(self.name)
  
  def isGood(self):
    if self.hist is None or type(self.hist) is TObject:
      warn(f"Could not find histogram: {self.name}")
      return False
    if self.hist.GetEntries() == 0:
      warn(f"Histogram is empty: {self.name}")
      return False
    
    return True
    
  def setup(self):
    self.hist.Rebin2D(self.x_rebin, self.y_rebin)

  def getName(self):
    return self.name + self.suffix
