import ROOT
from Sample import Sample, SampleType
from Legend import Legend
from Histogram import Histogram
from HistogramNormalizer import NormalizationType
from CmsLabelsManager import CmsLabel

samples = (
  Sample(
    name="DY",
    file_path="../samples/histograms/background_dy.root",
    type=SampleType.background,
    cross_section=0.4,
    line_alpha=0.0,
    fill_color=ROOT.kRed - 2,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="DY",
  ),
)
output_path = "../plots"

# fmt: off
histograms = (
  # name        title         logx   logy   norm_type                  rebin  xmin  xmax  ymin  ymax  xlabel         ylabel
  Histogram("Muon_pt" , "Muon p_{T}", False, True , NormalizationType.to_lumi,     5, None, None, None, None, "p_{T} [GeV]", "# events (2018)"),
  Histogram("Muon_eta", "Muon #eta" , False, False, NormalizationType.to_lumi,     5, None, None, None, None, "#eta"       , "# events (2018)"),
)
# fmt: on
luminosity = 63670.0  # pb^-1 (2018)

legends = {
  SampleType.background: Legend(0.7, 0.8, 0.85, 0.85, "f"),
}

plotting_options = {
  SampleType.background: "hist",
  SampleType.signal: "nostack hist",
  SampleType.data: "nostack e",
}

canvas_size = (800, 600)
show_ratio_plots = False
# ratio_limits = (0.7, 1.3)  # Optional override; limits are automatic by default.
