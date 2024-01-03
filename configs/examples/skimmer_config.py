nEvents = -1
printEveryNevents = 1000

inputFilePath = "../tea/samples/background_dy.root"
# or in case you run tea standalone, without specific analysis code:
# inputFilePath = "../samples/background_dy.root"

treeOutputFilePath = "./background_dy_skimmed.root"

weightsBranchName = "genWeight"

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

eventSelections = {
    "MET_pt": (30, 9999999),
    "nMuon": (1, 9999999),
    "nGoodLeptons": (1, 9999999),
}