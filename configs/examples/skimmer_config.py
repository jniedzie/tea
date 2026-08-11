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

# Branches to create on the output tree that do not exist in the input (see skimmer.cpp for
# where these are set via Event::SetFloat / PhysicsObject::SetFloat).
branchesToAdd = {
    "dimuonMass": ("Float_t", ""),
    "Muon_ptSquared": ("Float_t", "Muon"),
}

# Uncomment if you want to specify event weights (e.g. from MC generator):
# weightsBranchName = "genWeight"

# redirector = "xrootd-cms.infn.it"
