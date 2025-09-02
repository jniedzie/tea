# Task 5
#
# Objectives:
# - Create background and data histograms in a tt̄ CR.
# - Plot data/MC ratios.
#
# Hints:
# - Not much to change here, just define default histograms for TightMuons and GoodJets.
# - Most of the work is in the plotting script.
#   - Set file_name correctly.
#   - Comment out the Sample for the signal.
#   - Add a Sample for data. Use SampleType.data and set cross_section to 1.0. Adjust plotting style.
#   - Add Histograms for TightMuons and GoodJets pt and eta. Adjust y-axis ranges if needed.
#   - Use NormalizationType.to_data for these plots.
#   - Add plotting options/legends for data (use "pe").
#   - Turn on ratio plotting.

nEvents = -1

base_path = "/eos/home-j/jniedzie/tea_llp_das/samples/"

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
  "nTightMuons": (1, 1),
  "nLooseElectrons": (0, 0),
}

weightsBranchName = "genWeight"
eventsTreeNames = ["Events"]

# We add these lines to handle special branches in data nanoAOD that don't follow the convention
specialBranchSizes = {
    "Proton_multiRP": "nProton_multiRP",
    "Proton_singleRP": "nProton_singleRP",
}
