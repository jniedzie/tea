## specify how many events to run on (and how often to print current event number)
nEvents = 100
printEveryNevents = 10

# specify input/output paths 
inputFilePath = "input_tree.root"
histogramsOutputFilePath = "output_histograms.root"

# define default histograms (can be filled automatically with HistogramsFiller, based on collection and variable names)
defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
  ("Event"       , "nMuon"         , 50,     0,       50,      ""  ),
  ("Muon"        , "pt"            , 400,    0,       200,     ""  ),
  ("Muon"        , "eta"           , 100,    -2.5,    2.5,     ""  ),
)

# define custom histograms (you will have to fill them in your HistogramsFiller)
histParams = (
#    name         bins  xmin    xmax    dir
  ("m_inv",      1000,  0,      10,     "kinematics"),
  ("delta_phi",  1000, -3.5,    3.5,    "kinematics"),
  ("n_muons",    20,    0,      20,     "counters"  ),
)

# define custom 2D histograms (you will have to fill them in your HistogramsFiller)
histParams2D = (
#  name     bins_x  xmin  xmax bins_y ymin ymax     dir
  ("hit_xy", 100  , -20 , 20  , 100 , -20 , 20  ,   ""),
)

# specify name of the branch containing event weights
weightsBranchName = "genWeight"

eventsTreeNames = ["Events",]
specialBranchSizes = {
  "Particle": "Event_numberP",
}