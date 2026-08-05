from Histogram import Histogram
from HistogramNormalizer import NormalizationType
from Sample import Sample, SampleType

luminosity = 59820.

base_path = "../tea/samples/"
output_name = "../data/muonPtSFsTest2018.json"

collection = "Muon"
variable = "pt"

pt_edges = [0, 10, 20, 30] # 3 bins
histograms = {}
for i in range(len(pt_edges)-1):
    hist_name = f"{collection}_{variable}"
    histograms[f"pt_{i}"] = Histogram(
        name=hist_name,
        title=f"pt_{i}",
        norm_type=NormalizationType.to_lumi,
        x_min=pt_edges[i],
        x_max=pt_edges[i+1],
    )

# CorrectioWriter input
correction_name =  "muonPtSFsTest"
correction_description = "Test example scale factors for Muon pt"
correction_version = 1
correction_inputs = [
    {"name": "pt", "type": "real", "description": "Probe muon pt [GeV]"},
    {"name": "scale_factors", "type": "string", "description": "Choose nominal scale factor or one of the uncertainties"}
]
correction_output = {"name": "weight", "type": "real", "description": "Output scale factor (nominal) or uncertainty"}
correction_edges = [
    pt_edges,
    ["nominal", "up", "down"]
]
correction_flow = "error"

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
    name="ttZ", 
    file_path=f"{base_path}/histograms/signal_ttz.root", 
    type=SampleType.signal,
    cross_section=0.5407, 
  ),
  Sample(
    name="data", 
    file_path=f"{base_path}/histograms/data.root", 
    type=SampleType.data,
    cross_section=1, 
  ),
)
