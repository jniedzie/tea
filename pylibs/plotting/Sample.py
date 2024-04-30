import ROOT
from dataclasses import dataclass
from enum import Enum

from Legend import Legend
from Logger import error

# enum class with signal, background, data
class SampleType(Enum):
  background = 0
  data = 1
  signal = 2

@dataclass
class Sample:
  name: str = ""
  file_path: str = ""
  type: SampleType = SampleType.background
  cross_section: float = -1
  cross_sections: dict = None
  initial_weight_sum: float = -1
  line_color: int = ROOT.kBlack
  line_style: int = ROOT.kSolid
  line_alpha: float = 1.0
  line_width: int = 1
  marker_color: int = ROOT.kBlack
  marker_style: int = 20
  marker_size: float = 1.0
  fill_color: int = ROOT.kGreen
  fill_alpha: float = 0.7
  fill_style: int = 1001
  legend_description: str = ""
  plotting_options: str = ""
  custom_legend: Legend = None
  
  def __post_init__(self):
    if self.cross_sections is not None and self.cross_section < 0:
      if self.name in self.cross_sections:
        self.cross_section = self.cross_sections[self.name]
      elif "signal_" in self.name:
        self.cross_section = self.cross_sections[self.name.replace("signal_", "")]
      else:
        error(f"Sample {self.name} not found in cross sections dict")
        exit(0)
