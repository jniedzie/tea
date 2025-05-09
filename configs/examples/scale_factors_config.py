
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
    if year == "2022preEE":
      year_path = "2022_Summer22"
      pu_type = "Collisions2022_355100_357900_eraBCD_GoldenJson"
    if year == "2022postEE":
      year_path = "2022_Summer22EE"
      pu_type = "Collisions2022_359022_362760_eraEFG_GoldenJson"
  elif year == "2023preBPix" or year == "2023postBPix":
    run2 = False
    if year == "2023preBPix":
      year_path = "2023_Summer23"
      pu_type = "Collisions2023_366403_369802_eraBC_GoldenJson"
    if year == "2023postBPix":
      year_path = "2023_Summer23BPix"
      pu_type = "Collisions2023_369803_370790_eraD_GoldenJson"
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
    # systematic options: "central", "up/down_correlated" or "up/down_uncorrelated"
    "bTaggingMedium": {
      "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
      "type": "deepJet_mujets",
      "systematic": "central",
      "variations": "up_correlated,down_correlated,up_uncorrelated,down_uncorrelated",
      "workingPoint": "M",
      "jetID": "5",
    },
    "bTaggingTight": {
      "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
      "type": "deepJet_mujets",
      "systematic": "central",
      "variations": "up_correlated,down_correlated,up_uncorrelated,down_uncorrelated",
      "workingPoint": "T",
      "jetID": "5",
    },
        
    # Muon ID
    "muonIDLoose": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_LooseID_DEN_TrackerMuons", 
      "systematic": "nominal",
      "variations": "systup,systdown",
    },
    "muonIDMedium": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_MediumID_DEN_TrackerMuons", 
      "systematic": "nominal",
      "variations": "systup,systdown"
    },
    "muonIDTight": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_TightID_DEN_TrackerMuons", 
      "systematic": "nominal",
      "variations": "systup,systdown"
    },

    # Muon Iso
    "muonIsoLoose": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": loose_muon_iso_type,
      "systematic": "nominal",
      "variations": "systup,systdown"
    },
    "muonIsoTight": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": tight_muon_iso_type,
      "systematic": "nominal",
      "variations": "systup,systdown"
    },
    
    # Muon trigger
    "muonTriggerIsoMu24": {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight",
      "systematic": "nominal",
      "variations": "systup,systdown"
    },
    
    # Pileup
    "pileup": {
      "path": f"../tea/jsonPOG/POG/LUM/{year_path}/puWeights.json.gz",
      "type": f"{pu_type}",
      "systematic": "nominal",
      "variations": "",
    },
  }
  if run2: # No Run3 PUjetID SF yet
    scaleFactors["PUjetIDtight"] = {
      "path": f"../tea/jsonPOG/POG/JME/{year_path}/jmar.json.gz",
      "type": "PUJetID_eff",
      "systematic": "nom",
      "variations": "up,down",
      "workingPoint": "T",
    }
    #  Muon Reco no medium pt RECO SF for Run 3
    scaleFactors["muonReco"] = {
      "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
      "type": "NUM_TrackerMuons_DEN_genTracks",
      "systematic": "nominal",
      "variations": "systup,systdown",
    }
  if year == "2018": # TODO: add DSA SF for all years
    scaleFactors["dsamuonID"] = {
      "path": f"../tea/DSAMuonSF/2018_Z/NUM_DisplacedID_DEN_dSAMuons_abseta_pt_schemaV2.json.gz",
      "type": "NUM_DisplacedID_DEN_dSAMuons", 
      "year": "2018_preUL",
      "systematic": "sf",
      "variations": "",
    }
    scaleFactors["JpsiInvMassSFs"] = {
      "path": f"../data/JPsiCRsf2018.json",
      "type": "JpsiInvMassSFs",
      "systematic": "nominal",
      "variations": "up,down",
    }
  return scaleFactors
