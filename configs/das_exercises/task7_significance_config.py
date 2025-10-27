from Sample import Sample, SampleType
from Histogram import Histogram
from HistogramNormalizer import NormalizationType

# No need to change this path, you can use the pre-existing combine installation.
combine_path = "/afs/cern.ch/work/j/jniedzie/public/combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/"

skip_combine = False

# Definition of the input and output files and directories.
datacards_output_path = "../significance/datacards/"
plots_output_path = "../significance/plots/"
results_output_path = "../significance/results/"

# If True, poisson error on empty bins (1.84) will be added to data histograms. We can leave it False here.
add_uncertainties_on_zero = False

# Integrated luminosity for 2018 data-taking period.
luminosity = 2300000.

# If True, shapes (histograms) will be included in the datacards. This typically improves the sensitivity of the analysis.
include_shapes = True

background_samples = [
  Sample(
    name="tt_semi",
    file_path=f"../histograms_large_stat/background_ttsemileptonic_histograms.root",
    type=SampleType.background,
    cross_section=365.34,
  )
]

data_samples = [
  Sample(
    name="data_obs",
    file_path=f"../histograms_large_stat/collision_data_2018_histograms.root",
    type=SampleType.data,
    cross_section=1.0,
  )
]

signal_samples = [
  Sample(
    name=f"dummy_signal",
    file_path=f"../histograms_large_stat/tta_mAlp-30GeV_ctau-1e2mm_histograms.root",
    type=SampleType.signal,
    cross_section=1e-4,
  )
]

samples = data_samples + background_samples + signal_samples

# Decide which histogram to use for the limit calculation.
histogram = Histogram(name="Dimuon_minvAfterCut", norm_type=NormalizationType.to_lumi, x_max=100, rebin=1)

# List uncertainties (nuisance parameters) to be included in the datacard.
nuisances = {
    "lumi": {
        "data_obs": 1.017,  # arxiv.org/abs/2503.03946
        "tt_semi": 1.017,
    }
}

# Plotting parameters for the limit plot (brazil plot).
x_min = 1.0
x_max = 60.0

y_min = 1e-6
y_max = 1e-1

x_title = "m_{a} [GeV]"
y_title = "#sigma(pp #rightarrow t#bar{t}a) #times B(a #rightarrow #mu#mu) [pb]"
