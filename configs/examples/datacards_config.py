from Sample import Sample, SampleType
from Histogram import Histogram
from HistogramNormalizer import NormalizationType

base_path = "../samples/"
skim = ""

output_path = f"../datacards/limits_datacard"

# If True, poisson error on empty bins (1.84) will be added to data histograms
add_uncertainties_on_zero = False

samples = (
    Sample(
        name="DY",
        file_path=f"{base_path}/histograms/background_dy.root",
        type=SampleType.background,
        cross_section=1976.0,
    ),
    Sample(
        name="tt",
        file_path=f"{base_path}/histograms/background_tt.root",
        type=SampleType.background,
        cross_section=687.1,
    ),
    Sample(
        name="signal_ttZ",
        file_path=f"{base_path}/histograms/signal_ttz.root",
        type=SampleType.background,
        cross_section=0.5407,
    ),
    Sample(
        name="data_obs",
        file_path=f"{base_path}/histograms/data.root",
        type=SampleType.data,
    ),
)

# List histograms for which to create datacards 
histograms = [Histogram(name="Muon_pt", norm_type=NormalizationType.to_lumi)]

# List nuisance parameters (they will only be added for processes for which they were listed) 
nuisances = {
    "bck_syst": {
        "DY": 1.20,
        "tt": 1.20,
    },
    "signal_unc": {
        "signal_ttZ": 1.03,
    }
}
