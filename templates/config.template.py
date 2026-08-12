## specify how many events to run on (and how often to print current event number)
nEvents = 100

# specify input/output paths 
inputFilePath = "input_tree.root"
treeOutputFilePath = "output_tree.root"
histogramsOutputFilePath = "output_histograms.root"

# define default histograms (can be filled automatically with HistogramsFiller, based on collection and variable names)
defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
    ("Event"       , "nMuon"         , 50,     0,       50,      ""  ),
    ("Muon"        , "pt"            , 400,    0,       200,     ""  ),
    ("Muon"        , "eta"           , 100,    -2.5,    2.5,     ""  ),
)

# define custom histograms (you will have to fill them in your HistogramsFiller)
# title: (n_bins, min, max, "output_directory")
histParams = (
    ("m_inv",      1000,  0,      10,     "kinematics"),
    ("delta_phi",  1000, -3.5,    3.5,    "kinematics"),
    ("n_muons",    20,    0,      20,     "counters"  ),
)

# define custom 2D histograms (you will have to fill them in your HistogramsFiller)
# title: (n_bins_x, min_x, max_x, n_bins_y, min_y, max_y, "output_directory")
histParams2D = (
    ("hit_xy", 100, -20, 20, 100, -20, 20, ""),
)

# specify name of the branch containing event weights
weightsBranchName = "genWeight"
eventsTreeName = "Events"

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

# define simple event-level cuts
eventCuts = {
    "MET_pt": (30, 9999999),
    "nGoodLeptons": (1, 9999999),
    "nGoodJets": (4, 9999999),
    "nGoodBtaggedJets": (1, 9999999),
}

# you can add some custom parameters here
myParameter = 777

# In most cases branch size will be deduced automatically, but if you have some special cases, list them here
specialBranchSizes = {
    "Particle": "Event_numberP",
}

# First, branches to keep will be marked to be kept (empty tuple would result in no branches being kept)
branchesToKeep = (
    "*",
    # "Muon_*",
)

# then, on top of that, branches to remove will be marked to be removed (can be an empty tuple)
branchesToRemove = (
    "L1*",
    "HLT*",
    "Flag*",
    "SubJet",
)

# Branches to create on the output tree that do not exist in the input, values pulled from
# Event/PhysicsObject at fill time (Event::SetFloat/SetInt/..., PhysicsObject::SetFloat/SetInt/...).
# Added *after* CloneTree(0), so they are exempt from branchesToKeep / branchesToRemove above.
#   name: (ROOT type, collection)
# An empty collection means an event-level scalar; otherwise the branch is a per-object array
# indexed by that collection's size branch (must already exist on the output tree), and the value
# is read from each object's custom value named "<name minus the "<collection>_" prefix>".
# Supported types: Float_t, Double_t, Int_t, UInt_t, Bool_t, ULong64_t, UChar_t, Short_t, UShort_t.
branchesToAdd = {
    "dimuonMass": ("Float_t", ""),
    "Muon_dEdx": ("Float_t", "Muon"),
}
# branchesToAdd = {}
