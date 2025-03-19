
def get_scale_factors(year):
  run2 = True
  if year == "2016preVFP" or year == "2016postVFP":
    pu_type = "Collisions16_UltraLegacy_goldenJSON"
  elif year == "2017":
    pu_type = "Collisions17_UltraLegacy_goldenJSON"
  elif year == "2018":
    pu_type = "Collisions18_UltraLegacy_goldenJSON"
  elif year == "2022preEE" or year == "2022postEE":
    run2 = False
    pu_type = "Collisions2022_355100_357900_eraBCD_GoldenJson"
    if year == "2022preEE":
      year_path = "2022_Summer22"
    if year == "2022postEE":
      year_path = "2022_Summer22EE"
  elif year == "2023preBPix" or year == "2023postBPix":
    run2 = False
    pu_type = ""
    if year == "2023preBPix":
      year_path = "2023_Summer23"
    if year == "2023postBPix":
      year_path = "2023_Summer23BPix"
  else:
    error(f"Year {year} not supported.")

  if run2:
    year_path = f"{year}_UL"
    loose_muon_iso_type = "NUM_LooseRelIso_DEN_LooseID"
    tight_muon_iso_type = "NUM_TightRelIso_DEN_TightIDandIPCut"
  else:
    loose_muon_iso_type = "NUM_LoosePFIso_DEN_LooseID"
    tight_muon_iso_type = "NUM_TightPFIso_DEN_TightID"

  scaleFactors = {

    # b-tagging
    "bTaggingMedium": {
      "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
      "type": "deepJet_mujets",
      "systematic": "central",
      "workingPoint": "M",
      "jetID": "5",
    },
    "bTaggingTight": {
      "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
      "type": "deepJet_mujets",
      "systematic": "central",
      "workingPoint": "T",
      "jetID": "5",
    },
        
    # Muon ID
    "muonIDLoose": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_LooseID_DEN_TrackerMuons", 
      "ValType": "nominal",
    },
    "muonIDMedium": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_MediumID_DEN_TrackerMuons", 
      "ValType": "nominal",
    },
    "muonIDTight": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_TightID_DEN_TrackerMuons", 
      "ValType": "nominal",
    },

    # Muon Iso
    "muonIsoLoose": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": loose_muon_iso_type,
      "ValType": "nominal",
    },
    "muonIsoTight": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": tight_muon_iso_type,
      "ValType": "nominal",
    },
    
    # Muon trigger
    "muonTriggerIsoMu24": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight",
      "ValType": "nominal",
    },
    
    # Pileup
    "pileup": {
      "path": f"../tea/jsonPOG/POG/LUM/{year_path}/puWeights.json.gz",
      "type": f"{pu_type}",
      "weights": "nominal",
    },
  }
  if run2: # TODO: find if there should be run3 jetID SFs somewhere
    scaleFactors["jetIDtight"] = {
      "path": f"../tea/jsonPOG/POG/JME/{year_path}/jmar.json.gz",
      "type": "PUJetID_eff",
      "systematic": "nom",
      "workingPoint": "T",
    }
    #  Muon Reco no medium pt RECO SF for Run 3
    scaleFactors["muonReco"] = {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_TrackerMuons_DEN_genTracks",
      "ValType": "nominal",
    }
  if year == "2018": # TODO: add DSA SF for all years
    scaleFactors["dsamuonID"] = {
      "path": f"../tea/DSAMuonSF/2018_Z/NUM_DisplacedID_DEN_dSAMuons_abseta_pt_schemaV2.json.gz",
      "type": "NUM_DisplacedID_DEN_dSAMuons", 
      "year": "2018_preUL",
      "ValType": "sf",
    }
  return scaleFactors
