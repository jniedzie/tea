import ROOT
from ROOT import TColor

# base_path = "/nfs/dust/cms/user/jniedzie/ttalps_cms/"
base_path = "/Users/jeremi/Documents/Physics/DESY/ttalps_cms.nosync/data/"

input_paths = {
  "signal": f"{base_path}/signals/",
  "background": f"{base_path}/backgrounds/",
  "data": f"{base_path}/collision_data/",
}

output_path = "../plots"

# skim = ""
skim = "skimmed_looseSemileptonic"
# skim = "skimmed_signalLike"
# skim = "skimmed_ttbarLike"

# data&signals must be listed after backgrounds for now
files = {
  #name                  filename     type(signal/background)
  # "tta_mAlp-0p35GeV"  :  ["tta_mAlp-0p35GeV_skimmed_looseSemileptonic_hists.root", "signal"],
  # "TTJets"            :  ["TTJets_skimmed_looseSemileptonic_hists.root", "background"],
  # "TTbar_inclusive"   :  ["TT_skimmed_looseSemileptonic_hists.root", "background"],
  
  "ttZJets": ("EB2F627D-0570-7C4C-A561-C29B6E4F123A_hists.root", "background"),
  "ttHToMuMu": ("D41A5AFC-EC31-A64F-9E87-6F1C22ED6DCB_hists.root", "background"),
  "ttWJets": ("5B123882-8484-1B47-9A07-57F8F526F6EF_hists.root", "background"),
  # "ST_tW_top": ("776A38DC-FF27-6F4E-9B16-C55B696BAA92_hists.root", "background"),
  # "ST_tW_antitop": ("09B1D3CA-5FCC-0A48-BFA6-E1759D5D7D02_hists.root", "background"),
  # "TTbar_inclusive": ("FCA55055-C8F3-C44B-8DCC-6DCBC0B8B992_hists.root", "background"),
  
  
  # "QCD_Pt_30to50": ("72E0DD65-5D9D-3E47-99A9-AAB4E4ACC724_hists.root", "background"),
  # "QCD_Pt_50to80": ("CAB74055-4D6E-024F-9B89-465541A2B906_hists.root", "background"),
  # "QCD_Pt_80to120": ("5D2183A8-8AC4-7841-9308-A1A221F27EBC_hists.root", "background"),
  # "QCD_Pt_120to170": ("EFC4B90E-252D-5145-BE99-C880CAE3B061_hists.root", "background"),
  # "QCD_Pt_170to300": ("5C540F1F-6B0C-1047-B020-539529AB3BB6_hists.root", "background"),
  # "QCD_Pt_300to470": ("C5A7D337-F76C-B848-A17F-10BBBD72042B_hists.root", "background"),
  # "QCD_Pt_470to600": ("452A92CA-5CED-A944-A44F-54CBD68D33CE_hists.root", "background"),
  # "QCD_Pt_600to800": ("778F37B3-2E2D-024A-ADB2-66699F11783C_hists.root", "background"),
  # "QCD_Pt_800to1000": ("191A7BDE-A93B-9440-9BC9-A6BEE36F43EE_hists.root", "background"),
  # "QCD_Pt_1000to1400": ("C5C48DC6-E709-244D-B649-A6CC41B3F190_hists.root", "background"),
  # "QCD_Pt_1400to1800": ("99B44156-580D-0249-9241-9E88DF59F04B_hists.root", "background"),
  # "QCD_Pt_1800to2400": ("061D96A4-FE04-3348-9F8B-E7E9BA6E4327_hists.root", "background"),
  # "QCD_Pt_2400to3200": ("A937F1B0-3D60-4E4D-B9EF-F7882A82450E_hists.root", "background"),
  # "QCD_Pt_3200toInf": ("980542CA-9396-6344-88E3-EA9CCB639159_hists.root", "background"),
  
  "tta_mAlp-0p35GeV": ("tta_mAlp-0p35GeV_nEvents-100000_hists.root", "signal"),
  "SingleMuon2018": ("36ED9511-D46A-0C4F-A485-C2DF1C874906_hists.root", "data"),
}

color_palette = [
  TColor.GetColor(230, 159, 0),
  TColor.GetColor(86, 180, 233),
  TColor.GetColor(0, 158, 115),
  TColor.GetColor(0, 114, 178),
  TColor.GetColor(213, 94, 0),
]

luminosity_2018 = 63670. # pb^-1

# TODO: these are not perfect, verify them!
cross_sections = {
  #name                   cross section [pb]
  "TTbar_inclusive": 494.8, # that's for 14 TeV, not sure where to find the correct one...
  "ST_tW_top": 32.45,
  "ST_tW_antitop": 32.51,
  "ttWJets": 0.5407,
  "ttZJets": 0.4611,
  "ttHToMuMu": 0.5269,
  "QCD_Pt_30to50": 106800000.0,
  "QCD_Pt_50to80": 15720000.0,
  "QCD_Pt_80to120": 2363000.0,
  "QCD_Pt_120to170": 407600.0,
  "QCD_Pt_170to300": 104000.0,
  "QCD_Pt_300to470": 6806.0,
  "QCD_Pt_470to600": 552.0,
  "QCD_Pt_600to800": 154.6,
  "QCD_Pt_800to1000": 26.15,
  "QCD_Pt_1000to1400": 7.501,
  "QCD_Pt_1400to1800": 0.6419,
  "QCD_Pt_1800to2400": 0.0877,
  "QCD_Pt_2400to3200": 0.005241,
  "QCD_Pt_3200toInf": 0.0001346,
  
  "tta_mAlp-0p35GeV": 1,
  "SingleMuon2018": 1,
}

lines = {
  #name                   color
  # "tta_mAlp-0p35GeV"  :  [color_palette[0], ROOT.kSolid],
  # "TTbar_inclusive"   :  [33, ROOT.kSolid],
  # "TTJets"            :  [36, ROOT.kSolid],
  
  "TTbar_inclusive": [33, ROOT.kSolid],
  "ST_tW_top": [38, ROOT.kSolid],
  "ST_tW_antitop": [30, ROOT.kSolid],
  "ttWJets": [ROOT.kMagenta, ROOT.kSolid],
  "ttZJets": [41, ROOT.kSolid],
  "ttHToMuMu": [50, ROOT.kSolid],
  "QCD_Pt_30to50": [60, ROOT.kSolid],
  "QCD_Pt_50to80": [61, ROOT.kSolid],
  "QCD_Pt_80to120": [62, ROOT.kSolid],
  "QCD_Pt_120to170": [63, ROOT.kSolid],
  "QCD_Pt_170to300": [64, ROOT.kSolid],
  "QCD_Pt_300to470": [65, ROOT.kSolid],
  "QCD_Pt_470to600": [66, ROOT.kSolid],
  "QCD_Pt_600to800": [67, ROOT.kSolid],
  "QCD_Pt_800to1000": [68, ROOT.kSolid],
  "QCD_Pt_1000to1400": [69, ROOT.kSolid],
  "QCD_Pt_1400to1800": [70, ROOT.kSolid],
  "QCD_Pt_1800to2400": [71, ROOT.kSolid],
  "QCD_Pt_2400to3200": [72, ROOT.kSolid],
  "QCD_Pt_3200toInf": [73, ROOT.kSolid],
  "tta_mAlp-0p35GeV": [color_palette[0], ROOT.kSolid],
  "SingleMuon2018": [ROOT.kBlack, ROOT.kSolid],
} 

legends = {
  #name                   color
  # "tta_mAlp-0p35GeV"  :  "m_{a} = 0.35 GeV",
  # "TTbar_inclusive"   :  "t#bar{t} incl.",
  # "TTJets"            :  "t#bar{t} + jets",
  
  "TTbar_inclusive": "TTbar_inclusive",
  "ST_tW_top": "ST_tW_top",
  "ST_tW_antitop": "ST_tW_antitop",
  "ttWJets": "ttWJets",
  "ttZJets": "ttZJets",
  "ttHToMuMu": "ttHToMuMu",
  "QCD_Pt_30to50": "QCD_Pt_30to50",
  "QCD_Pt_50to80": "QCD_Pt_50to80",
  "QCD_Pt_80to120": "QCD_Pt_80to120",
  "QCD_Pt_120to170": "QCD_Pt_120to170",
  "QCD_Pt_170to300": "QCD_Pt_170to300",
  "QCD_Pt_300to470": "QCD_Pt_300to470",
  "QCD_Pt_470to600": "QCD_Pt_470to600",
  "QCD_Pt_600to800": "QCD_Pt_600to800",
  "QCD_Pt_800to1000": "QCD_Pt_800to1000",
  "QCD_Pt_1000to1400": "QCD_Pt_1000to1400",
  "QCD_Pt_1400to1800": "QCD_Pt_1400to1800",
  "QCD_Pt_1800to2400": "QCD_Pt_1800to2400",
  "QCD_Pt_2400to3200": "QCD_Pt_2400to3200",
  "QCD_Pt_3200toInf": "QCD_Pt_3200toInf",
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
  "muon_leading_pt" :    ("",          True,   "to_background",   5,       0,       500,     -1,    -1,    "Leading p_{T}^{#mu} [GeV]",  "# events (2018)"  ),
  "muon_subleading_pt" : ("",          True,   "to_background",   5,       0,       500,     -1,    -1,    "All subleading p_{T}^{#mu} [GeV]",  "# events (2018)"  ),
  "muon_eta"  :          ("",          True,   "to_background",   10,      -3.5,    3.5,     1e0,    1e10,    "#eta^{#mu}",         "# events (2018)"  ),
  "muon_dxy"  :          ("",          True,   "to_background",   2,       -10,     10,      -1,    -1,    "d_{xy}^{#mu}",       "# events (2018)"  ),
  "muon_dz"   :          ("",          True,   "to_background",   2,       -10,     10,      -1,    -1,    "d_{z}^{#mu}",        "# events (2018)"  ),
  "n_eles"    :          ("",          True,   "to_background",   1,       0,       10,      1e0,    1e8,    "Number of electrons","# events (2018)"  ),
  "ele_pt"    :          ("",          True,   "to_background",   5,       0,       500,     10,    1e8,    "p_{T}^{e} [GeV]",    "# events (2018)"  ),
  # "ele_leading_pt"    :  ("",          True,   "to_background",   5,       0,       200,     -1,    -1,    "Leading p_{T}^{e} [GeV]",    "# events (2018)"  ),
  # "ele_subleading_pt"  : ("",          True,   "to_background",   5,       0,       200,     -1,    -1,    "All subleading p_{T}^{e} [GeV]",    "# events (2018)"  ),
  "ele_eta"   :          ("",          False,   "norm1",   10,      -3.5,    3.5,     0,    1,    "#eta^{e}",           "# events (2018)"  ),
  "ele_dxy"   :          ("",          True,   "to_background",   2,       -10,     10,      -1,    -1,    "d_{xy}^{e}",         "# events (2018)"  ),
  "ele_dz"    :          ("",          True,   "to_background",   2,       -10,     10,      -1,    -1,    "d_{z}^{e}",          "# events (2018)"  ),
  "n_jets"    :          ("",          True,   "to_background",   1,       0,       30,      1e0,   1e9,    "Number of jets",     "# events (2018)"  ),
  "jet_pt"    :          ("",          True,   "to_background",   5,       0,       500,     10,    1e8,    "p_{T}^{j} [GeV]",    "# events (2018)"  ),
  "jet_eta"   :          ("",          True,   "to_background",   10,      -3.5,    3.5,     1e0,    1e10,    "#eta^{j}",           "# events (2018)"  ),
  "jet_btagDeepB":       ("",          True,   "to_background",   2,       -1,      1,       -1,    -1,    "jet btagDeepB",      "# events (2018)"  ),
  "cutFlow"   :          ("cutflow",   True,   "to_background",  1,       0,       7,       -1,    -1,    "Selection",          "Number of events"  ),
}

efficiency_plots = {
# key                     from hist  title                  xlabel       ylabel
  "cutFlowEfficiency":   ("cutFlow", "Cutflow efficiency",  "Selection", "Number of events"  ),
}
