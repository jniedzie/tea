## specify how many events to run on (and how often to print current event number)
nEvents = 100

# specify input/output paths
inputFilePath = "../tea/samples/background_dy.root"
histogramsOutputFilePath = "../samples/histograms/custom_histograms.root"

# define default histograms (can be filled automatically with HistogramsFiller, based on collection and variable names)
# fmt: off
defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
  ("Event"       , "nMuon"         , 50,     0,       50,      ""  ),
  ("Muon"        , "pt"            , 400,    0,       200,     ""  ),
  ("Muon"        , "eta"           , 100,    -2.5,    2.5,     ""  ),
)

# define custom histograms (you will have to fill them in your HistogramsFiller)
histParams = (
#  collection variable    bins  xmin    xmax    dir
  ("Dimuon", "mInv",      1000,  0,      10,     "kinematics"),
  ("Dimuon", "deltaPhi",  1000, -3.5,    3.5,    "kinematics"),
)

# define custom 2D histograms (you will have to fill them in your HistogramsFiller)
histParams2D = (
#  name     bins_x  xmin  xmax bins_y ymin ymax     dir
  ("hit_xy", 100  , -20 , 20  , 100 , -20 , 20  ,   ""),
)
# fmt: on

# specify name of the branch containing event weights
weightsBranchName = "genWeight"

eventsTreeNames = [
  "Events",
]
specialBranchSizes = {
  "Particle": "Event_numberP",
}
