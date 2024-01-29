from Logger import *

from dataclasses import dataclass
from ROOT import TObject

@dataclass
class Histogram:
  name: str = ""
  title: str = ""
  log_x: bool = False
  log_y: bool = False
  norm_type: str = "norm1"
  rebin: int = 1
  x_min: float = 0.0
  x_max: float = 0.0
  y_min: float = 0.0
  y_max: float = 0.0
  x_label: str = ""
  y_label: str = ""
  suffix: str = ""
  
  def __post_init__(self):
    self.hist = None
  
  def getName(self):
    return self.name + self.suffix
  
  def print(self):
    info(f"Histogram {self.name}, {self.hist}")
  
  def load(self, input_file):
    self.hist = input_file.Get(self.name)
  
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

@dataclass
class Histogram2D:
  name: str = ""
  title: str = ""
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
