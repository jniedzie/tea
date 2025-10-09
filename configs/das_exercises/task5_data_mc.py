# The number of events to process. -1 means all events.
nEvents = -1

base_path = "/eos/cms/store/group/committee_schools/2025-cmsdas-hamburg/llp/samples/"

process = "background_ttsemileptonic"
# process = "collision_data_2018"

inputFilePath = f"{base_path}/{process}/output_0.root"
histogramsOutputFilePath = f"../histograms/{process}/ttCR.root"

defaultHistParams = (
  #  collection      variable          bins    xmin     xmax     dir
  ("Event", "nMuon", 50, 0, 50, ""),
  # TODO: add histograms for tight muon and good jet eta and pt
)

# Collections defined here can be used in other parts of the python configs, and in the C++ code.
extraEventCollections = {
  "TightMuons": {
    "inputCollections": ["Muon"],
    "pt": (30., 9999999.),
    "eta": (-2.4, 2.4),
    "pfRelIso04_all": (0., 0.15),
    "tightId": True,
  },
  "LooseElectrons": {
    "inputCollections": ["Electron"],
    "pt": (15., 9999999.),
    "eta": (-2.5, 2.5),
    "mvaFall17V2Iso_WPL": True,
  },
  "GoodJets": {
    "inputCollections": ["Jet"],
    "pt": (30., 9999999.),
    "eta": (-2.4, 2.4),
    "jetId": 6,
  },
}

# These event selections can be applied to standard nanoAOD branches and custom collections defined above.
eventCuts = {
  "MET_pt": (50, 9999999),
  # TODO: add tigher event cuts
}

weightsBranchName = "genWeight"
eventsTreeNames = ["Events"]

# We add these lines to handle special branches in data nanoAOD that don't follow the convention
specialBranchSizes = {
    "Proton_multiRP": "nProton_multiRP",
    "Proton_singleRP": "nProton_singleRP",
}
