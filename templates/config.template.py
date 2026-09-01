# specify how many events to run on (and how often to print current event number)
nEvents = 100

# specify input/output paths
inputFilePath = "input_tree.root"
treeOutputFilePath = "output_tree.root"
histogramsOutputFilePath = "output_histograms.root"

# define default histograms (can be filled automatically with HistogramsFiller, based on collection and variable names)
# fmt: off
defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
    ("Event"                , "nMuon"   , 50  , 0   , 50,  ""),
    ("Muon"                 , "pt"      , 400 , 0   , 200, ""),
    ("Muon"                 , "eta"     , 100 , -2.5, 2.5, ""),
    ("NonGlobalMuons"       , "isGlobal", 2   , -0.5, 1.5, ""),
    ("NonGlobalMuonsByRange", "isGlobal", 2   , -0.5, 1.5, ""),
)

# define custom histograms (you will have to fill them in your HistogramsFiller)
histParams = (
#    collection variable       bins  xmin  xmax  dir
    ("Dimuon"   , "mInv"      , 1000, 0   , 10  , "kinematics"),
    ("Dimuon"   , "deltaPhi"  , 1000, -3.5, 3.5 , "kinematics"),
    ("Counters" , "nMuons"    , 20  , 0   , 20  , "counters"  ),
)

# define custom 2D histograms (you will have to fill them in your HistogramsFiller)
# title: (n_bins_x, min_x, max_x, n_bins_y, min_y, max_y, "output_directory")
histParams2D = (
  ("hit_xy", 100, -20, 20, 100, -20, 20, ""),
)
# fmt: on

# specify name of the branch containing event weights
weightsBranchName = "genWeight"
eventsTreeName = "Events"

# define extra collections:
# - give it a name: e.g. GoodLeptons
# - specify inputCollections: only those will be looped over to create your new collection
# - add requirements on values: a two-value tuple is an inclusive numeric range,
#   while a single integer selects that exact value. In particular, (0, 0) and 0
#   both select only objects whose field is zero.
extraEventCollections = {
  "GoodLeptons": {
    "inputCollections": ("Muon", "Electron"),
    "pt": (30.0, 9999999.0),
    "eta": (-2.4, 2.4),
  },
  "GoodBtaggedJets": {
    "inputCollections": ("Jet",),
    "pt": (30.0, 9999999.0),
    "eta": (-2.4, 2.4),
    "btagDeepB": (0.5, 9999999.0),
  },
  "NonGlobalMuons": {
    "inputCollections": ("Muon",),
    "isGlobal": 0,
  },
  "NonGlobalMuonsByRange": {
    "inputCollections": ("Muon",),
    "isGlobal": (0, 0),
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

# Branches to create on the output tree that don't exist in the input: (collection, name, ROOT
# type, varexp). Empty varexp means the branch is app-set only, via Event::Set<T>/PhysicsObject::Set<T>.
# Custom values live for one event only, so anything the app doesn't set again is written as zero.
# fmt: off
branchesToAdd = (
  ("Event", "dimuonMass"  , "Float_t"         , "-1.0"),
  ("Muon" , "dEdx"        , "Float_t"         , ""    ),
  ("Event", "looseMuonPt" , "vector<Float_t>" , ""    ),
)
# fmt: on
# branchesToAdd = ()
