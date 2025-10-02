# Task 3
#
# Objectives:
# - Pre-select events with at least 2 tight muons.
# - Drop all branches except for Muon and PatMuonVertex collections
#
# Hints:
# - Muon branches start with "Muon_*" and dimuon branches start with "PatMuonVertex_*".

nEvents = -1

base_path = "/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/samples/"

process = "tta_mAlp-12GeV_ctau-1e2mm"

inputFilePath = f"{base_path}/{process}/output_0.root"
treeOutputFilePath = f"../trees/{process}/skimmed.root"


# Collections defined here can be used in other parts of the python configs, and in the C++ code.
extraEventCollections = {
  "TightMuons": {
    "inputCollections": ["Muon"],
    "pt": (30., 9999999.),
    "eta": (-2.4, 2.4),
    "pfRelIso04_all": (0., 0.15),
    "tightId": True,
  },
}

# These event selections can be applied to standard nanoAOD branches and custom collections defined above.
eventCuts = {
  "MET_pt": (50, 9999999),
  # TODO: add requirement of at least 2 tight muons
}

weightsBranchName = "genWeight"

# TODO: drop all branches except for Muon and PatMuonVertex collections
branchesToKeep = []
