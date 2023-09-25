nEvents = -1
printEveryNevents = 1000

inputFilePath = "/afs/desy.de/user/l/lrygaard/TTALP/ttalps_cms/tta_mAlp-0p35GeV_skimmed_looseSemileptonic.root"
histogramsOutputFilePath = "./tta_mAlp-0p35GeV_nEvents-100000.root"

defaultHistParams = {
# key              collection    variable      bins    xmin     xmax    outputdir  
  "n_muons"   :   ("Event",      "nMuon",      50,     0,       50,      ""  ),
  "muon_pt"   :   ("Muon",       "pt",         400,    0,       200,     ""  ),
  "muon_eta"  :   ("Muon",       "eta",        100,    -2.5,    2.5,     ""  ),
  "muon_dxy"  :   ("Muon",       "dxy",        400,    -20,     20,      ""  ),
  "muon_dz"   :   ("Muon",       "dz",         400,    -20,     20,      ""  ),
  "n_eles"    :   ("Event",      "nElectron",  50,     0,       50,      ""  ),
  "ele_pt"    :   ("Electron",   "pt",         400,    0,       200,     ""  ),
  "ele_eta"   :   ("Electron",   "eta",        100,    -2.5,    2.5,     ""  ),
  "ele_dxy"   :   ("Electron",   "dxy",        400,    -20,     20,      ""  ),
  "ele_dz"    :   ("Electron",   "dz",         400,    -20,     20,      ""  ),
  "n_jets"    :   ("Event",      "nJet",       50,     0,       50,      ""  ),
  "jet_pt"    :   ("Jet",        "pt",         400,    0,       200,     ""  ),
  "jet_eta"   :   ("Jet",        "eta",        100,    -2.5,    2.5,     ""  ),
  "jet_eta"   :   ("Jet",        "eta",        100,    -2.5,    2.5,     ""  ),
  "jet_btagDeepB":("Jet",        "btagDeepB",  200,    -1,      1,       ""  ),
}


defaultHistVariables = {key: (params[0],params[1]) for key, params in defaultHistParams.items()}

histParams = {key : value for histParams in (defaultHistParams,) for key,value in histParams.items()}

histTitles = {key: key for key, params in histParams.items()}
histNbins = {key: params[2] for key, params in histParams.items()}
histMin = {key: params[3] for key, params in histParams.items()}
histMax = {key: params[4] for key, params in histParams.items()}
histOutputDir = {key: params[5] for key, params in histParams.items()}