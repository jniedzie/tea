
scaleFactors = {
  # jets
  "jetIDtight": {
    "path": "../tea/jsonPOG/POG/JME/2018_UL/jmar.json.gz",
    "type": "PUJetID_eff",
    "systematic": "nom",
    "workingPoint": "T",
  },
  
  # b-tagging
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
    "systematic": "central",
    "workingPoint": "T",
    "jetID": "5",
  },
  
  #  Muon Reco
  "muonReco": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_TrackerMuons_DEN_genTracks",
    "year": "2018_UL",
    "ValType": "nominal",
  },
  
  # Muon ID
  "muonIDLoose": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_LooseID_DEN_TrackerMuons", 
    "year": "2018_UL",
    "ValType": "nominal",
  },
  "muonIDMedium": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_MediumID_DEN_TrackerMuons", 
    "year": "2018_UL",
    "ValType": "nominal",
  },
  "muonIDTight": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_TightID_DEN_TrackerMuons", 
    "year": "2018_UL",
    "ValType": "nominal",
  },
  "dsamuonID": {
    "path": "../tea/DSAMuonSF/2018_Z/NUM_DisplacedID_DEN_dSAMuons_abseta_pt_schemaV2.json.gz",
    "type": "NUM_DisplacedID_DEN_dSAMuons", 
    "year": "2018_preUL",
    "ValType": "sf",
  },
  
  # Muon Iso
  "muonIsoLoose": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_LooseRelIso_DEN_LooseID",
    "year": "2018_UL",
    "ValType": "nominal",
  },
  "muonIsoTight": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_TightRelIso_DEN_TightIDandIPCut",
    "year": "2018_UL",
    "ValType": "nominal",
  },
  
  # Muon trigger
  "muonTriggerIsoMu24": {
    "path": "../tea/jsonPOG/POG/MUO/2018_UL/muon_Z.json.gz",
    "type": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight",
    "year": "2018_UL",
    "ValType": "nominal",
  },
  
  # Pileup
  "pileup": {
    "path": "../tea/jsonPOG/POG/LUM/2018_UL/puWeights.json.gz",
    "type": "Collisions18_UltraLegacy_goldenJSON",
    "weights": "nominal",
  },
}