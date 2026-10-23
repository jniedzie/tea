from Sample import Sample, SampleType
from Histogram import Histogram
from HistogramNormalizer import NormalizationType
from LimitPlotter import PlotOptions

base_path = "../samples/"
skim = ""

limits_output_path = "../limits/ttz-limits-example"
output_formats = ["pdf", "png"]

# If True, poisson error on empty bins (1.84) will be added to data histograms
add_uncertainties_on_zero = False

signal_samples = (
  Sample(
    name="signal_ttZ",
    file_path=f"{base_path}/histograms/signal_ttz.root",
    type=SampleType.signal,
    cross_section=0.5407,
  ),
)

# fmt: off
background_samples = (
  Sample(name="DY", file_path=f"{base_path}/histograms/background_dy.root", type=SampleType.background, cross_section=1976.0),
  Sample(name="tt", file_path=f"{base_path}/histograms/background_tt.root", type=SampleType.background, cross_section=687.1 ),
)
# fmt: on

data_samples = (Sample(name="data_obs", file_path=f"{base_path}/histograms/data.root", type=SampleType.data),)
samples = signal_samples + background_samples + data_samples

# List histograms for which to create datacards
histogram = Histogram(name="Muon_pt", norm_type=NormalizationType.to_lumi)

# List nuisance parameters (they will only be added for processes for which they were listed)
nuisances = {
  "bck_syst": {
    "DY": 1.20,
    "tt": 1.20,
  },
  "signal_unc": {
    "signal_ttZ": 1.03,
  },
}

# Producer contract: use complete identities and explicit scan coordinates, independent of names.
signal_points = {
  "signal_ttZ": {"id": "ttZ_nominal", "x": 1.0, "parameters": {"model": "ttZ"}, "nominal_cross_section": 0.5407},
}
include_shapes = True
luminosity = 59700.0  # pb^-1; use the luminosity corresponding to your input files.
blind = True
skip_combine = False
combine_setup = "cmsenv"  # Run in your Combine environment, or replace with its setup command.

plot_options = PlotOptions(
  x_title="Model point",
  y_title="95% CL upper limit on r",
  reference="r1",
  luminosity=luminosity / 1000,
  annotations=("ttZ example",),
)
