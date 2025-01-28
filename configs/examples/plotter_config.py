import ROOT
from ROOT import TColor
from Sample import Sample, SampleType
from Legend import Legend
from Histogram import Histogram, Histogram2D
from HistogramNormalizer import NormalizationType

base_path = "../samples/"
skim = ""

output_path = "../plots"

luminosity = 63670. # pb^-1 (2018)

samples = (
  Sample(
    name="DY", 
    file_path=f"{base_path}/histograms/background_dy.root", 
    type=SampleType.background,
    cross_section=1976.0, 
    line_alpha=0.0,
    fill_color=41,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="Drell-Yan (2018)",
    # if you add a custom legend for this sample, it will override the default legend.
    # custom_legend = Legend(0.5, 0.5, 0.7, 0.8, "f"),
  ),
  Sample(
    name="tt", 
    file_path=f"{base_path}/histograms/background_tt.root", 
    type=SampleType.background,
    cross_section=687.1, 
    line_alpha=0.0,
    fill_color=42,
    fill_alpha=0.7,
    marker_size=0.0,
    legend_description="tt semi-leptonic (2018)",
    # custom_legend = Legend(0.7, 0.5, 0.9, 0.8, "f"),
  ),
  Sample(
    name="ttZ", 
    file_path=f"{base_path}/histograms/signal_ttz.root", 
    type=SampleType.signal,
    cross_section=0.5407, 
    # line_alpha=0.0,
    line_color=TColor.GetColor(230, 159, 0), 
    line_style=ROOT.kSolid,
    # fill_color=TColor.GetColor(230, 159, 0), 
    fill_alpha=0.0,
    marker_size=0.0,
    legend_description="ttZ+jets (2018)"
  ),
  Sample(
    name="data", 
    file_path=f"{base_path}/histograms/data.root", 
    type=SampleType.data,
    cross_section=1, 
    line_color=ROOT.kBlack,
    line_style=ROOT.kSolid,
    marker_style=20,
    marker_size=1.0,
    marker_color=ROOT.kBlack,
    fill_alpha=0.0,
    legend_description="data (2018)"
  ),
)

# You can specify custom order for stacks. If you don't, they will be ordered by cross-section
# custom_stacks_order = ("DY", "tt", "ttZ", "data")

y_label = "# events (2018)"

histograms = (
#           name                  title logy    norm_type                       rebin xmin   xmax  ymin    ymax,    xlabel                ylabel            suffix
  Histogram("Event_nMuon"         , "", False , NormalizationType.to_data, 1  ,   0   , 20  , 1e1   , 5e4   , "Number of muons"   , y_label           ),
  Histogram("Event_nMuon"         , "", True  , NormalizationType.to_data, 1  ,   0   , 20  , 1e1   , 1e9   , "Number of muons"   , y_label          , "_log" ),
  Histogram("Muon_pt"             , "", True  , NormalizationType.to_data, 5  ,   0   , 500 , 1e-2  , 1e3   , "p_{T}^{#mu} [GeV]" , y_label           ),
  Histogram("Muon_eta"            , "", False , NormalizationType.to_data, 10 , -3.5  , 3.5 , 1e0   , 1e3   , "#eta^{#mu}"        , y_label          , "_log" ),
  Histogram("Muon_eta"            , "", True  , NormalizationType.to_data, 10 , -3.5  , 3.5 , 1e0   , 1e3   , "#eta^{#mu}"        , y_label           ),
  Histogram("Event_nGoodLeptons"  , "", True  , NormalizationType.to_data, 1  ,   0   , 30  , 1e0   , 1e9   , "Number of jets"    , y_label           ),
  Histogram("GoodLeptons_pt"      , "", True  , NormalizationType.to_data, 5  ,   0   , 500 , 10    , 1e8   , "p_{T}^{j} [GeV]"   , y_label           ),
  Histogram("GoodLeptons_eta"     , "", True  , NormalizationType.to_data, 10 , -3.5  , 3.5 , 1e0   , 1e10  , "#eta^{j}"          , y_label           ),
  Histogram("cutFlow"             , "", True  , NormalizationType.to_data, 1  ,   0   , 8   , 1e2   , 1e6   , "Selection"         , "#sum genWeight"  ),
)

histograms2D = (
#           name              title                rebin  xmin    xmax       ymin   ymax     zmin zmax xlabel               ylabel                        zlabel
  # Histogram2D("hit_xy",         "hit_xy"          , 1, 1, -15     , 15      , -15   , 15    , 0,  1e5, "x"             , "y"                         , "Counts"),
  # Histogram2D("time_vs_toa",    "time_vs_toa"     , 1, 1, -10     , 100     , -10   , 2000  , 0,  1e3, "Time (ns)"     , "Time of Arrival (ToA)"     , "Counts"),
)

legend_width = 0.15
legend_min_x = 0.40
legend_max_x = 0.80

legend_height = 0.05
legend_max_y = 0.85

n_signal = len([s for s in samples if s.type == SampleType.signal and s.custom_legend is None])
n_data = len([s for s in samples if s.type == SampleType.data and s.custom_legend is None])
n_background = len([s for s in samples if s.type == SampleType.background and s.custom_legend is None])

# here default legends per sample type are defined. If you want to override them, specify custom_legend in the sample
legends = {
  SampleType.signal     : Legend(legend_min_x               , legend_max_y - n_signal*legend_height           , legend_min_x+legend_width , legend_max_y                        , "l" ),
  SampleType.data       : Legend(legend_min_x               , legend_max_y - (n_signal+n_data)*legend_height  , legend_min_x+legend_width , legend_max_y-n_signal*legend_height , "pl"),
  SampleType.background : Legend(legend_max_x-legend_width  , legend_max_y - n_background*legend_height       , legend_max_x              , legend_max_y                        , "f" ),
}

plotting_options = {
  SampleType.background: "hist",
  SampleType.signal: "nostack e",
  SampleType.data: "nostack pe",
}

output_formats = ["pdf", ".png"]

canvas_size = (800, 600)
show_ratio_plots = True
ratio_limits = (0.7, 1.3)

