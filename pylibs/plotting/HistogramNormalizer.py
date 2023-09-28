from enum import Enum
from ROOT import TFile
from Sample import SampleType

class NormalizationType(Enum):
  to_one = 0 # normalize all histograms to 1
  to_background = 1 # normalize background with cross section and luminosity, normalize signal and data to background

class HistogramNormalizer:
  
  def __init__(self, config):
    self.config = config
    
    total_backgrounds_entries, total_backgrounds_integral, total_backgrounds_cross_section = self.__getTotalBackgroundsIntegral()
    self.total_backgrounds_entries = total_backgrounds_entries
    self.total_backgrounds_integral = total_backgrounds_integral
    self.total_backgrounds_cross_section = total_backgrounds_cross_section
  
  def normalize(self, hist, sample):
    lumi = self.config.luminosity
    
    if hist.norm_type == "norm1":
      if sample.type == SampleType.background:
        hist.hist.Scale(lumi*sample.cross_section/self.total_backgrounds_integral)
      else:
        hist.hist.Scale(1./hist.Integral())
    elif hist.norm_type == "to_background":
      if sample.type == SampleType.background:
        # TODO: should do this one properly, dividing by initial number of events
        hist.hist.Scale(lumi*sample.cross_section/hist.hist.Integral())
      else:
        hist.hist.Scale(lumi*self.total_backgrounds_cross_section/hist.hist.Integral())
        
  def __getTotalBackgroundsIntegral(self):
    entries = 0
    integral = 0
    cross_section = 0
    
    for sample in self.config.samples:
      if sample.type != SampleType.background:
        continue
      
      file = TFile.Open(sample.file_path, "READ")

      hist_name = next(iter(self.config.histograms)).name
      hist = file.Get(hist_name) 

      integral += hist.Integral() * self.config.luminosity * sample.cross_section
      entries += hist.Integral()
      cross_section += sample.cross_section
      
    return entries, integral, cross_section