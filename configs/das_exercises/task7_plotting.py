import ROOT
from Sample import Sample, SampleType
from Legend import Legend
from Histogram import Histogram
from HistogramNormalizer import NormalizationType

luminosity = 2300000.  # pb^-1 (2018)

samples = [
  Sample(
    name="tt_semi",
    file_path="../histograms_large_stat/background_ttsemileptonic_histograms.root",
    type=SampleType.background,
    cross_section=365.34,
    line_alpha=1.0,
    line_color=ROOT.kRed - 2,
    fill_color=ROOT.kRed - 2,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="tt semi-leptonic",
  ),
  Sample(
    name="data",
    file_path="../histograms_large_stat/collision_data_2018_histograms.root",
    type=SampleType.data,
    cross_section=1.0,
    line_alpha=1,
    line_style=1,
    fill_alpha=0,
    marker_size=1,
    marker_style=20,
    line_color=ROOT.kBlack,
    legend_description="2018 data",
  ),
]

output_path = "../plots_large_stat/"

histograms = (
  #            name      title     logx   logy    norm_type                  rebin xmin xmax ymin ymax  xlabel         ylabel
  Histogram("Dimuon_minvAfterCut", "", False, True, NormalizationType.to_lumi, 5, 0, 100, 1e-1, 1e2, "m_{inv}^{#mu#mu} [GeV]", "# events"),
  Histogram("Dimuon_logLxy", "", False, True, NormalizationType.to_lumi, 3, -4, 3, 1e-1, 1e4, "log(L_{xy}^{#mu#mu} [cm])", "# events"),
)

legends = {
  SampleType.background: Legend(0.5, 0.85, 0.78, 0.90, "f"),
  SampleType.data: Legend(0.5, 0.8, 0.78, 0.85, "pe"),
}

plotting_options = {
  SampleType.background: "hist",
  SampleType.signal: "nostack hist",
  SampleType.data: "pe",
}

canvas_size = (800, 600)

show_ratio_plots = True
ratio_limits = (0.0, 5.0)
