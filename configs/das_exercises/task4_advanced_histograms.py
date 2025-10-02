# Task 4
#
# Objectives:
# - Apply selections that will mostly keep events with tt̄ + 2 muons.
# - Create a histogram of the best dimuon candidate invariant mass.
# - Look at the dimuon L_xy and apply a cut on it to enhance ALP signal.
#
# Hints:
# - We will need custom collections for loose/tight muons and for loose electrons.
#    Some of them are already implemented, but you will need to add a collection for loose muons.
# - You will need to apply some basic event cuts. Some are already implemented, but you should
#    require zero loose electrons and at least 3 loose muons.
# - NanoDimuonVertex class has a method called GetLxyFromPV that may be useful.

nEvents = -1

base_path = "/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/samples/"

process = "background_ttsemileptonic"
# process = "tta_mAlp-12GeV_ctau-1e2mm"

inputFilePath = f"{base_path}/{process}/output_0.root"
histogramsOutputFilePath = f"../histograms/{process}/after_selections.root"

defaultHistParams = (
  #  collection      variable          bins    xmin     xmax     dir
  ("Event", "nMuon", 50, 0, 50, ""),
  ("Muon", "pt", 400, 0, 200, ""),
  ("Muon", "eta", 100, -2.5, 2.5, ""),
)

# Here, we define a custom histogram for the invariant mass of the best dimuon candidate.
# Dimuon_minv is not a standard nanoAOD collection, so we will have to fill this one manually in a C++ program.
histParams = (
  # collection      variable          bins    xmin     xmax     dir
  # TODO: create a histogram for the invariant mass of the best dimuon candidate
  # TODO: add other needed histograms
)

# Collections defined here can be used in other parts of the python configs, and in the C++ code.
extraEventCollections = {
  "TightMuons": {
    "inputCollections": ["Muon"],
    "pt": (30., 9999999.),
    "eta": (-2.4, 2.4),
    "pfRelIso04_all": (0., 0.15),
    "tightId": True,
  },
  "LooseMuons": {
    "inputCollections": ["Muon"],
    # TODO: define selection criteria for loose muons.
    # Loose muons have p_T > 3 GeV, |η| < 2.5, and should have the "looseId" flag.
  },
  "LooseElectrons": {
    "inputCollections": ("Electron", ),
    "pt": (15., 9999999.),
    "eta": (-2.5, 2.5),
    "mvaFall17V2Iso_WPL": True,
  },
}

# These event selections can be applied to standard nanoAOD branches and custom collections defined above.
eventCuts = {
  "MET_pt": (50, 9999999),
  "nTightMuons": (1, 9999999),
  # TODO: add requirements of 0 electrons and at least 3 loose muons
}

weightsBranchName = "genWeight"
