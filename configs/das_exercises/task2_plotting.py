# Task 2
#
# Objectives:
# - Use the plotter to create nice plots of muon pT and η distributions in tt semileptonic and one of the signal samples.
# - Understand different plotting options.
#
# Hints:
# - There's not much to do here, you only need to specify your input paths.
# - Try to understand everything in this script though, as we will use it a few times.
# - You can play with different settings to see how the plots change.
# - Try different normalization options: NormalizationType.to_lumi, NormalizationType.to_one, NormalizationType.none. If you do that, you'll have to adjust y-axis ranges.

import ROOT
from Sample import Sample, SampleType
from Legend import Legend
from Histogram import Histogram
from HistogramNormalizer import NormalizationType

luminosity = 63670.  # pb^-1 (2018)

samples = (
  Sample(
    name="tt_semi",
    file_path="...",  # your path should go here
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
    name="alp_12_1e2",
    file_path="...",  # your path should go here
    type=SampleType.signal,
    cross_section=0.001,
    line_alpha=1,
    line_style=1,
    fill_alpha=0,
    marker_size=0,
    marker_style=0,
    line_color=ROOT.kBlue,
    legend_description="ALP 12 GeV, c#tau = 100 mm",
  ),
)
output_path = "../plots/"

histograms = (
  #         name      title logx   logy   norm_type                  rebin  xmin  xmax ymin   ymax xlabel         ylabel
  Histogram("Muon_pt" , "", False, True , NormalizationType.to_lumi, 4,     0   , 200, 1    , 1e3, "p_{T}^{#mu} [GeV]", "# events"),
  Histogram("Muon_eta", "", False, False, NormalizationType.to_lumi, 4,     -2.4, 2.4, 0    , 250, "#eta^{#mu}"       , "# events"),
)

legends = {
  SampleType.background: Legend(0.5, 0.8, 0.78, 0.85, "f"),
  SampleType.signal: Legend(0.5, 0.7, 0.78, 0.75, "l"),
}

plotting_options = {
  SampleType.background: "hist",
  SampleType.signal: "nostack hist",
  SampleType.data: "nostack e",
}

canvas_size = (800, 600)

show_ratio_plots = False
ratio_limits = (0.7, 1.3)
