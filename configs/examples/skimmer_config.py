nEvents = -1

inputFilePath = "../tea/samples/background_dy.root"
treeOutputFilePath = "../samples/skimmed/background_dy.root"

triggerSelection = (
    "HLT_IsoMu24",
)

extraEventCollections = {
    "GoodLeptons": {
        "inputCollections": ("Muon", "Electron"),
        "pt": (30., 9999999.),
        "eta": (-2.4, 2.4),
    },
}

eventCuts = {
    "MET_pt": (30, 9999999),
    "nMuon": (1, 9999999),
    "nGoodLeptons": (1, 9999999),
}


# First, branches to keep will be marked to be kept (empty tuple would result in no branches being kept)
# branchesToKeep = (
#     "*",
#     # "Muon_*",
# )

# then, on top of that, branches to remove will be marked to be removed (can be an empty tuple)
# branchesToRemove = (
#     "L1*",
#     "HLT*",
#     "Flag*",
#     "SubJet",
# )

# Branches to create on the output tree that do not exist in the input: (collection, name, ROOT
# type, varexp). dimuonMass is app-set only (see skimmer.cpp), "-1.0" is just its constant
# fallback default. Muon_ptSquared is config-computed from Muon_pt via varexp.
# Can be overwritten in the app
branchesToAdd = (
    ("Event", "dimuonMass", "Float_t", "-1.0"),
    ("Muon", "ptSquared", "Float_t", "Muon_pt**2"),
    ("Event", "muonPt", "vector<Float_t>", ""),
)

# Uncomment if you want to specify event weights (e.g. from MC generator):
# weightsBranchName = "genWeight"

# redirector = "xrootd-cms.infn.it"
