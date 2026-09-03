nEvents = -1

inputFilePath = "../tea/samples/background_dy.root"
treeOutputFilePath = "../samples/skimmed/background_dy.root"

triggerSelection = ("HLT_IsoMu24",)

extraEventCollections = {
  "GoodLeptons": {
    "inputCollections": ("Muon", "Electron"),
    "pt": (30.0, 9999999.0),
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

# See templates/config.template.py for the (collection, name, type, varexp) format.
branchesToAdd = (
  ("Event", "dimuonMass", "Float_t", "-1.0"),
  ("Muon", "ptSquared", "Float_t", "Muon_pt**2"),
  ("Muon", "ptIfGood", "Float_t", ""),
  ("Event", "muonPt", "vector<Float_t>", ""),
)

# Uncomment if you want to specify event weights (e.g. from MC generator):
# weightsBranchName = "genWeight"

# The xrootd door used whenever a path in this config is a bare LFN ("/store/...").
# EventReader prepends "root://<redirector>/" before opening such a path, and the
# submitter uses the same value to list an input directory with `xrdfs ls`. Prefer the
# site-local door when there is one -- it avoids a redirect hop -- and fall back to a
# federation redirector otherwise. Left unset, tea uses TEA_XROOTD_REDIRECTOR
# (default "cms-xrd-global.cern.ch") and EventReader tries its own built-in list.
# redirector = "cms-xrd-global.cern.ch"    # or e.g. "maite.iihe.ac.be:1094"

# Where output is staged to, when it does not land on a local filesystem. Defaults to
# TEA_STAGE_URL_BASE (itself defaulting to the IIHE door); setting it here instead makes
# a submission self-describing rather than dependent on the submitter's environment.
# stage_url_base = "davs://maite.iihe.ac.be:2880"
