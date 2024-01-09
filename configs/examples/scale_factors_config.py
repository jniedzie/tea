from ScaleFactorsReader import ScaleFactorsReader
from Logger import *

import os
import urllib.request
import gzip

scaleFactorsReader = ScaleFactorsReader()

muonSFs = {
  # Reco SFs
  **scaleFactorsReader.getMuonScaleFactors("../tea/data/muon_SFs/muon_highPt_recoID.json"),
  **scaleFactorsReader.getMuonScaleFactors("../tea/data/muon_SFs/NUM_TrackerMuons_DEN_genTracks_Z_abseta_pt.json"),
  **scaleFactorsReader.getMuonScaleFactors("../tea/data/muon_SFs/Efficiency_muon_generalTracks_Run2018_UL_trackerMuon.json"),

  # ID SFs
  **scaleFactorsReader.getMuonScaleFactors("../tea/data/muon_SFs/Efficiency_muon_trackerMuon_Run2018_UL_ID.json"),
  **scaleFactorsReader.getMuonScaleFactors("../tea/data/muon_SFs/Efficiencies_muon_generalTracks_Z_Run2018_UL_ID.json"),

  # Iso SFs
  **scaleFactorsReader.getMuonScaleFactors("../tea/data/muon_SFs/Efficiencies_muon_generalTracks_Z_Run2018_UL_ISO.json"),

  # Trigger SFs
  **scaleFactorsReader.getMuonTriggerScaleFactors("../tea/data/muon_SFs/Efficiencies_muon_generalTracks_Z_Run2018_UL_SingleMuonTriggers_schemaV2.json"),
}

bTaggingSFs = {
  # B-tagging SFs
  **scaleFactorsReader.getBtaggingScaleFactors("../tea/data/b_tagging/btagging_UL2018.json"),
}

muonSFsPath = "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz"

scaleFactors = {
  "bTaggingMedium": {
    "path": "../tea/jsonPOG/POG/BTV/2018_UL/btagging.json.gz",
    "type": "deepJet_mujets",
    "systematic": "central",
    "workingPoint": "M",
    "jetID": "5",
  },
  "bTaggingTight": {
    "path": "../tea/jsonPOG/POG/BTV/2018_UL/btagging.json.gz",
    "type": "deepJet_mujets",
    "workingPoint": "T",
    "systematic": "central",
    "workingPoint": "M",
    "jetID": "5",
  },
  
  "muonReco": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_TrackerMuons_DEN_genTracks",
    "year": "2018_UL",
    "ValType": "sf",
  },
  
  "muonIDLoose": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_LooseID_DEN_TrackerMuons", 
    "year": "2018_UL",
    "ValType": "sf",
  },
  "muonIDMedium": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_MediumID_DEN_TrackerMuons", 
    "year": "2018_UL",
    "ValType": "sf",
  },
  "muonIDTight": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_TightID_DEN_TrackerMuons", 
    "year": "2018_UL",
    "ValType": "sf",
  },
  
  "muonIsoLoose": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_LooseRelIso_DEN_LooseID",
    "year": "2018_UL",
    "ValType": "sf",
  },
  "muonIsoTight": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_TightRelIso_DEN_TightIDandIPCut",
    "year": "2018_UL",
    "ValType": "sf",
  },
  
  "muonTriggerIsoMu24": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight",
    "year": "2018_UL",
    "ValType": "sf",
  },
  
  
}