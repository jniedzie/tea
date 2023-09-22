## specify how many events to run on (and how often to print current event number)
nEvents = 100
printEveryNevents = 10

# specify input/output paths 
inputFilePath = "input_tree.root"
treeOutputFilePath = "output_tree.root"
histogramsOutputFilePath = "output_histograms.root"

# define histograms
# key: ("title", n_bins, min, max, "output_directory")
histParams = {
    "m_inv": ("m_inv", 1000, 0, 10, "kinematics"),
    "delta_phi": ("delta_phi", 1000, -3.5, 3.5, "kinematics"),
    "n_muons": ("n_muons", 20, 0, 20, "counters"),
}

# define extra collections:
# - give it a name: e.g. GoodLeptons
# - specify inputCollections: only those will be looped over to create your new collection
# - add some requirements on values: e.g. if input collections have fields called pt, i.e. Muon_pt and Electron_pt, 
# you can specify a range for this parameter
extraEventCollections = {
    "GoodLeptons": {
        "inputCollections": ("Muon", "Electron"),
        "pt": (30., 9999999.),
        "eta": (-2.4, 2.4),
    },
    "GoodBtaggedJets": {
        "inputCollections": ("Jet", ),
        "pt": (30., 9999999.),
        "eta": (-2.4, 2.4),
        "btagDeepB": (0.5, 9999999.),
    },
}

# define simple event-level selections
eventSelections = {
    "MET_pt": (30, 9999999),
    "nGoodLeptons": (1, 9999999),
    "nGoodJets": (4, 9999999),
    "nGoodBtaggedJets": (1, 9999999),
}

# you can add some custom parameters here
myParameter = 777

# leave this part as is - it converts the histograms dictionary to a form easier to digest by the parser
histTitles = {key: params[0] for key, params in histParams.items()}
histNbins = {key: params[1] for key, params in histParams.items()}
histMin = {key: params[2] for key, params in histParams.items()}
histMax = {key: params[3] for key, params in histParams.items()}
histOutputDir = {key: params[4] for key, params in histParams.items()}
