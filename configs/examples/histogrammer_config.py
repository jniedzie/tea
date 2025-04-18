from scale_factors_config import *

year = "2018"
# options for year is: 2016preVFP, 2016postVFP, 2017, 2018, 2022preEE, 2022postEE, 2023preBPix, 2023postBPix
scaleFactors = get_scale_factors(year)

nEvents = -1
printEveryNevents = 1000

inputFilePath = "../tea/samples/background_dy.root"
# or in case you run tea standalone, without specific analysis code:
# inputFilePath = "../samples/background_dy.root"

histogramsOutputFilePath = "./background_dy_histograms.root"

extraEventCollections = {
    "GoodLeptons": {
        "inputCollections": ("Muon", "Electron"),
        "pt": (30., 9999999.),
        "eta": (-2.4, 2.4),
    },
}


defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
  ("Event"       , "nMuon"         , 50,     0,       50,      ""  ),
  ("Muon"        , "pt"            , 400,    0,       200,     ""  ),
  ("Muon"        , "eta"           , 100,    -2.5,    2.5,     ""  ),
  ("Event"       , "nGoodLeptons"  , 50,     0,       50,      ""  ),
  ("GoodLeptons" , "pt"            , 400,    0,       200,     ""  ),
  ("GoodLeptons" , "eta"           , 100,    -2.5,    2.5,     ""  ),
)

histParams = (
  ("Muon", "scaledPt", 400, 0, 200, ""),
)

weightsBranchName = "genWeight"
applyMuonScaleFactors = True
applyMuonTriggerScaleFactors = True

SFvariationVariables = ["Muon_pt"]
