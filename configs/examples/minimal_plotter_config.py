import ROOT
from Sample import Sample, SampleType
from Legend import Legend
from Histogram import Histogram
from HistogramNormalizer import NormalizationType
from CmsLabelsManager import CmsLabel

year = "2018"
show_cms_labels = True
label_outside_axes = True
# plot_margins = {"left": 0.16, "right": 0.17, "top": 0.09, "bottom": 0.2}

# Allowed labels: paper, paper_sim, paper_supplementary, paper_sim_supplementary, pas, pas_sim, pas_supplementary,
# pas_sim_supplementary, thesis, thesis_sim, private_data_sim, private_data, private_sim.
cms_label = CmsLabel.paper_sim_supplementary

samples = (
  Sample(
    name="DY",
    file_path="../samples/histograms/background_dy.root",
    type=SampleType.background,
    cross_section=0.4,
    line_alpha=0.0,
    fill_color=ROOT.kRed-2,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="DY"
  ),
)
output_path = "../plots"

histograms = (
#            name            title     logx   logy    norm_type                  rebin xmin xmax ymin ymax  xlabel         ylabel
  Histogram("Muon_pt" , "Muon p_{T}",  False, True,   NormalizationType.to_lumi, 5,   None  , None,  None,   None , "p_{T} [GeV]", "# events (2018)"),
  Histogram("Muon_eta", "Muon #eta",   False, False,  NormalizationType.to_lumi, 5,  None, None,  None,   None  , "#eta"       , "# events (2018)"),
)
luminosity = 63670.  # pb^-1 (2018)

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
