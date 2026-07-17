# scaleFactors: optional dict that maps scale-factor names to their correctionlib configuration.
# When absent (or empty), no scale factors are applied and all event weights default to 1.0.
#
# Each entry has the form:
#   "<name>": {
#     "path":        "<path to correctionlib JSON(.gz) file>",
#     "type":        "<correction name inside the file>",
#     "systematic":  "<key for the nominal value>",      # e.g. "nominal", "central", "nom"
#     "variations":  "<comma-separated variation keys>", # e.g. "up,down" or "systup,systdown"
#     # additional keys are correction-specific, e.g.:
#     # "workingPoint": "M", "flavour": "5", "level": "L1L2L3Res", "algo": "AK4PFchs"
#   }
#
# See configs/examples/scale_factors_config.py for a full set of standard CMS scale factors
# and the list of names recognised by NanoEventProcessor (bTaggingMedium, muonIDTight,
# pileup, L1PreFiringWeight, jecMC, jerMC_ScaleFactor, ...).
#
# To use the standard set, uncomment the lines below:
# from scale_factors_config import get_scale_factors
# year = "2018"
# # options for year: 2016preVFP, 2016postVFP, 2017, 2018, 2022preEE, 2022postEE, 2023preBPix, 2023postBPix
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

histParams = (
  ("Muon", "scaledPt", 400, 0, 200, ""),
  ("Muon", "someUnfilledHistogram", 400, 0, 200, ""),
)

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
