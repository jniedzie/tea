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
  luminosity: float = -1
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
  year: int = -1

  def __post_init__(self):
    if self.cross_sections is not None and self.cross_section < 0:

      name = self.name.replace("signal_", "")

      for key, cross_section in self.cross_sections.items():
        if name in key:
          self.cross_section = cross_section
          break
      else:
        fatal(f"Sample {name} not found in cross sections dict")
        exit(1)
