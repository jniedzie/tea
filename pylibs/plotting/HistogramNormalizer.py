from enum import Enum
from ROOT import TFile, TObject
from Sample import SampleType
from Logger import *

class NormalizationType(Enum):
  to_one = 0 # normalize all histograms to 1
  to_background = 1 # normalize background with cross section and luminosity, normalize signal and data to background
  to_lumi = 2 # normalize signal/background to lumi*crosssection, keep data unchanged
  to_data = 3 # normalize signal/background to data, keep data unchanged
  none = 4 # do not normalize

class HistogramNormalizer:
  
  def __init__(self, config):
    self.config = config
    
    # Check if any of histograms in the config chas NormalizationType different than none or to_one:
    normalize_hists = False
    for hist in self.config.histograms:
      if hist.norm_type != NormalizationType.none and hist.norm_type != NormalizationType.to_one:
        normalize_hists = True
        break
    
    if normalize_hists:
      self.__setBackgroundEntries()
  
  def normalize(self, hist, sample, data_integral=None, background_integral=None):
    if hist.norm_type == NormalizationType.to_one:
      self.__normalizeToOne(hist, sample, background_integral)
    elif hist.norm_type == NormalizationType.to_background:
      self.__normalizeToBackground(hist, sample, background_integral)
    elif hist.norm_type == NormalizationType.to_lumi:
      self.__normalizeToLumi(hist, sample)
    elif hist.norm_type == NormalizationType.to_data:
      self.__normalizeToData(hist, sample, data_integral)
  
  def __normalizeToOne(self, hist, sample):
    if sample.type == SampleType.background:
      hist.hist.Scale(1./self.total_background)
    else:
      hist.hist.Scale(1./hist.hist.Integral())
  
  def __normalizeToBackground(self, hist, sample, background_integral):
    if sample.type == SampleType.background:
      hist.hist.Scale(self.config.luminosity*sample.cross_section/self.background_initial_sum_weights[sample.name])
    elif sample.type == SampleType.signal:
      hist.hist.Scale(background_integral/hist.hist.Integral())
    elif sample.type == SampleType.data:
      hist.hist.Scale(background_integral/self.data_final_entries[sample.name])
  
  def __normalizeToLumi(self, hist, sample):
    scale = self.config.luminosity*sample.cross_section
    
    if sample.type == SampleType.background:
      scale /= self.background_initial_sum_weights[sample.name]
    elif sample.type == SampleType.signal:
      scale /= self.signal_final_sum_weights[sample.name]
    elif sample.type == SampleType.data:
      scale = 1
    
    hist.hist.Scale(scale)
  
  def __normalizeToData(self, hist, sample, data_integral):
    if hist.hist.Integral() == 0:
      error(f"Couldn't normalize to data: {hist.name}, {sample.name}")
      return  
    if data_integral is None:
      error(f"Couldn't normalize to data: {hist.name}, {sample.name}")
      return
    
    scale = data_integral/hist.hist.Integral()
    
    if sample.type == SampleType.background:
      scale *= sample.cross_section/self.total_background_cross_section
    elif sample.type == SampleType.data:  
      scale = 1
    
    hist.hist.Scale(scale)
  
  def __setBackgroundEntries(self):
    
    self.signal_final_sum_weights = {}
    self.data_final_entries = {}
    self.background_final_sum_weights = {}
    self.background_initial_sum_weights = {}
    self.total_background = 0
    self.total_background_cross_section = 0
    
    for sample in self.config.samples:
      file = TFile.Open(sample.file_path, "READ")

      cut_flow = file.Get("cutFlow")
      
      if cut_flow is None or type(cut_flow) == TObject:
        error(f"Couldn't find cut flow histogram for sample {sample.name}")
        continue
      
      initial_weight_sum = cut_flow.GetBinContent(1)
      final_weight_sum = cut_flow.GetBinContent(cut_flow.GetNbinsX())
      
      if initial_weight_sum == 0:
        efficiency = 0
      else:
        efficiency = final_weight_sum/initial_weight_sum
      
      if sample.type == SampleType.background:
        self.total_background += sample.cross_section * self.config.luminosity * efficiency
        self.background_initial_sum_weights[sample.name] = initial_weight_sum
        self.background_final_sum_weights[sample.name] = final_weight_sum
        
        if final_weight_sum != 0:
          self.total_background_cross_section += sample.cross_section
        else:
          warn(f"Sample {sample.name} has no events after cuts, consider removing it from the config")
        
        
      elif sample.type == SampleType.signal:
        self.signal_final_sum_weights[sample.name] = final_weight_sum
        
      elif sample.type == SampleType.data:
        self.data_final_entries[sample.name] = final_weight_sum
