from Sample import Sample, SampleType
from Histogram import Histogram
from HistogramNormalizer import NormalizationType
from LimitPlotter import PlotOptions

# No need to change this path, you can use the pre-existing combine installation.
combine_path = "/afs/cern.ch/work/j/jniedzie/public/combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/"

# You can use this to skip the combine step (e.g., if you already have the combine output and just want to put a few of them together).
skip_combine = False

# Definition of the input and output files and directories.
file_name = "after_selections.root"
limits_output_path = "../limits"

# If True, poisson error on empty bins (1.84) will be added to data histograms. We can leave it False here.
add_uncertainties_on_zero = False

# Integrated luminosity for 2018 data-taking period.
luminosity = 63670.0  # pb^-1 (2018)

# If True, shapes (histograms) will be included in the datacards. This typically improves the sensitivity of the analysis.
include_shapes = True

# This is an arbitrary reference value. The actual limit will be calculated relative to this.
# The only important thing is that it's not crazy small or crazy large - in such case combine may run into numerical issues.
# In general, adjust it such that the signal strength reported from combine is around 1
# (0.01 or 100 is still fine, but 1e-10 or 1e6 may cause problems).
reference_cross_section = 1e-4

# Define the complete point metadata alongside the scan parameters.
signal_points = {
  f"alp_{mass}_1e2": {
    "id": f"alp_{mass}_1e2",
    "x": mass,
    "parameters": {"mass": mass, "ctau": 100.0},
    "nominal_cross_section": reference_cross_section,
  }
  for mass in (1, 2, 12, 30, 60)
}

# Definition of signal and background samples.
signal_samples = [
  Sample(
    name=name,
    file_path=f"../histograms/tta_mAlp-{point['parameters']['mass']}GeV_ctau-1e2mm/{file_name}",
    type=SampleType.signal,
    cross_section=point["nominal_cross_section"],
  )
  for name, point in signal_points.items()
]

background_samples = [
  Sample(
    name="tt_semi",
    file_path=f"../histograms/background_ttsemileptonic/{file_name}",
    type=SampleType.background,
    cross_section=365.34,
  )
]

samples = signal_samples + background_samples

# Decide which histogram to use for the limit calculation.
histogram = Histogram(
  name="",  # TODO: pick the histogram to use
  norm_type=NormalizationType.to_lumi,
  x_max=100,
  rebin=1,
)

# List uncertainties (nuisance parameters) to be included in the datacard.
nuisances = {
  "lumi": {
    "signal": 1.017,  # arxiv.org/abs/2503.03946
    "tt_semi": 1.017,
  }
}

# Plotting parameters for the limit plot (Brazil plot).
plot_options = PlotOptions(
  x_title="m_{a} [GeV]",
  y_title="#sigma(pp #rightarrow t#bar{t}a) #times B(a #rightarrow #mu#mu) [pb]",
  x_range=(1.0, 60.0),
  y_range=(1e-6, 1e-1),
  log_x=True,
  log_y=True,
  quantity="cross_section",
  reference="nominal",
  luminosity=luminosity / 1000,
)
