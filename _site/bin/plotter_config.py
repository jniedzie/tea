import ROOT
from ROOT import TColor

base_path = "/Users/jeremi/Documents/Physics/DESY/ttalps_cms.nosync/data/"

input_paths = {
  "signal": f"{base_path}/signals/",
  "background": f"{base_path}/backgrounds/",
  "data": f"{base_path}/collision_data/",
}

output_path = "../plots"

skim = "skimmed_looseSemileptonic"

# data&signals must be listed after backgrounds for now
files = {
  #name                  filename     type(signal/background)
  "ttZJets": ("EB2F627D-0570-7C4C-A561-C29B6E4F123A_hists.root", "background"),
  "ttHToMuMu": ("D41A5AFC-EC31-A64F-9E87-6F1C22ED6DCB_hists.root", "background"),
  
  "tta_mAlp-0p35GeV": ("tta_mAlp-0p35GeV_nEvents-100000_hists.root", "signal"),
  "SingleMuon2018": ("36ED9511-D46A-0C4F-A485-C2DF1C874906_hists.root", "data"),
}

luminosity_2018 = 63670. # pb^-1

cross_sections = {
  #name                   cross section [pb]
  "ttZJets": 0.4611,
  "ttHToMuMu": 0.5269, 
  "tta_mAlp-0p35GeV": 1,
  "SingleMuon2018": 1,
}

lines = {
  #name                   color
  "ttZJets": [41, ROOT.kSolid],
  "ttHToMuMu": [50, ROOT.kSolid],
  
  "tta_mAlp-0p35GeV": [TColor.GetColor(230, 159, 0), ROOT.kSolid],
  "SingleMuon2018": [ROOT.kBlack, ROOT.kSolid],
} 

legends = {
  #name                   color
  "ttZJets": "ttZJets",
  "ttHToMuMu": "ttHToMuMu",

  "tta_mAlp-0p35GeV":"tta_mAlp-0p35GeV",
  "SingleMuon2018": "SingleMuon2018",
}

legend_types = {
  "signal": "l",
  "background": "f",
  "data": "pl",
}

legend_position = {
  "signal": (0.15,0.85,0.25,0.89),
  "background": (0.7,0.5,0.85,0.85),
  "data": (0.15,0.8,0.25,0.85),
}

# normalization options:
#   norm1: normalize to 1
#   to_background: normalize background with cross section and luminosity, 
#                  normalize signal and data to background

variables = {
# key                    title         logy   norm_type   rebin    xmin     xmax     ymin,  ymax,  xlabel                 ylabel
  "n_muons"   :          ("",          True,   "to_background",   1,       0,       20,      1e1,    1e9,    "Number of muons",    "# events (2018)"  ),
  "muon_pt"   :          ("",          True,   "to_background",   5,       0,       500,     1e2,    1e8,    "p_{T}^{#mu} [GeV]",  "# events (2018)"  ),
  "muon_eta"  :          ("",          True,   "to_background",   10,      -3.5,    3.5,     1e0,    1e10,    "#eta^{#mu}",         "# events (2018)"  ),
  "n_jets"    :          ("",          True,   "to_background",   1,       0,       30,      1e0,   1e9,    "Number of jets",     "# events (2018)"  ),
  "jet_pt"    :          ("",          True,   "to_background",   5,       0,       500,     10,    1e8,    "p_{T}^{j} [GeV]",    "# events (2018)"  ),
  "jet_eta"   :          ("",          True,   "to_background",   10,      -3.5,    3.5,     1e0,    1e10,    "#eta^{j}",           "# events (2018)"  ),
  "cutFlow"   :          ("cutflow",   True,   "to_background",  1,       0,       7,       -1,    -1,    "Selection",          "Number of events"  ),
}

efficiency_plots = {
# key                     from hist  title                  xlabel       ylabel
  "cutFlowEfficiency":   ("cutFlow", "Cutflow efficiency",  "Selection", "Number of events"  ),
}
