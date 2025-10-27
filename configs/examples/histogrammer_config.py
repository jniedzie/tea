# If you want to apply scale factors, uncomment this:
# from scale_factors_config import get_scale_factors
# year = "2018"
# # options for year is: 2016preVFP, 2016postVFP, 2017, 2018, 2022preEE, 2022postEE, 2023preBPix, 2023postBPix
# scaleFactors = get_scale_factors(year)

nEvents = -1

inputFilePath = "../tea/samples/background_dy.root"
histogramsOutputFilePath = "../samples/histograms/background_dy.root"

extraEventCollections = {
  "GoodLeptons": {
    "inputCollections": ("Muon", "Electron"),
    "pt": (30., 9999999.),
    "eta": (-2.4, 2.4),
  },
}

defaultHistParams = (
  #  collection      variable          bins    xmin     xmax     dir
  ("Event", "nMuon", 50, 0, 50, ""),
  ("Muon", "pt", 400, 0, 200, ""),
  ("Muon", "eta", 100, -2.5, 2.5, ""),
  ("Event", "nGoodLeptons", 50, 0, 50, ""),
  ("GoodLeptons", "pt", 400, 0, 200, ""),
  ("GoodLeptons", "eta", 100, -2.5, 2.5, ""),
)

histParams = (("Muon", "scaledPt", 400, 0, 200, ""), )

# Uncomment this if your events tree has a name other than "Events" (or if you have multiple trees):
# eventsTreeNames = [
#   "myEvents",
#   "myOtherEvents",
# ]

# You can uncomment this if the name of a branch containing the size of a collection has some non-standard name:
# specialBranchSizes = {
#     "Particle": "Event_numberP",
# }

# Uncomment if you want to specify event weights (e.g. from MC generator):
# weightsBranchName = "genWeight"
