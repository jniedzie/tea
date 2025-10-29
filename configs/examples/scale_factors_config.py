
from Logger import error


def get_scale_factors(year):
  run2 = True
  if year == "2016preVFP" or year == "2016postVFP":
    pu_type = "Collisions16_UltraLegacy_goldenJSON"
    muon_trigger_type = "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    jecType = "Summer19UL16_V7_MC"
    jecAlgo = "AK4PFchs"
    jecYear = "2016"
    if year == "2016preVFP":
      jecType = "Summer19UL16APV_V7_MC"
  elif year == "2017":
    pu_type = "Collisions17_UltraLegacy_goldenJSON"
    jecType = "Summer19UL17_V5_MC"
    jecAlgo = "AK4PFchs"
    jecYear = "2017"
    muon_trigger_type = "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight"
  elif year == "2018":
    pu_type = "Collisions18_UltraLegacy_goldenJSON"
    jecType = "Summer19UL18_V5_MC"
    jecAlgo = "AK4PFchs"
    jecYear = "2018"
    muon_trigger_type = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
  elif year == "2022preEE" or year == "2022postEE":
    run2 = False
    muon_trigger_type = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    if year == "2022preEE":
      year_path = "2022_Summer22"
      pu_type = "Collisions2022_355100_357900_eraBCD_GoldenJson"
      jecType = "Summer22_22Sep2023_V2_MC"
      jecAlgo = "AK4PFPuppi"
      jecYear = "2022"
    if year == "2022postEE":
      year_path = "2022_Summer22EE"
      pu_type = "Collisions2022_359022_362760_eraEFG_GoldenJson"
      jecType = "Summer22EE_22Sep2023_V2_MC"
      jecAlgo = "AK4PFPuppi"
      jecYear = "2022"
  elif year == "2023preBPix" or year == "2023postBPix":
    run2 = False
    muon_trigger_type = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    if year == "2023preBPix":
      year_path = "2023_Summer23"
      pu_type = "Collisions2023_366403_369802_eraBC_GoldenJson"
      jecType = "Summer23Prompt23_V1_MC"
      jecAlgo = "AK4PFPuppi"
      jecYear = "2023"
    if year == "2023postBPix":
      year_path = "2023_Summer23BPix"
      pu_type = "Collisions2023_369803_370790_eraD_GoldenJson"
      jecType = "Summer23BPixPrompt23_V1_MC"
      jecAlgo = "AK4PFPuppi"
      jecYear = "2023"
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

      # Pileup
      "pileup": {
          "path": f"../tea/jsonPOG/POG/LUM/{year_path}/puWeights.json.gz",
          "type": f"{pu_type}",
          "systematic": "nominal",
          "variations": "up,down",
      },

      # Dimuon Eff. SFs from tt+JPsi CR - WIP
      # "dimuonEff": {
      #     # "path": f"../tea/data/dimuonEffSFs/dimuonEffSFs{year}.json", 
      #     "type": "dimuonEff",
      #     "systematic": "nominal",
      #     "variations": "up,down",
      # },

      # Muon trigger
      "muonTrigger": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": muon_trigger_type,
          "systematic": "nominal",
          "variations": "systup,systdown"
      },

      # DSA Muon SFs
      "dsamuonID": {
          "path": f"../tea/DSAMuonSF/{jecYear}_Jpsi/NUM_DisplacedID_DEN_dSAMuons_abseta_pt_schemaV2.json.gz",
          "type": "NUM_DisplacedID_DEN_dSAMuons",
          "systematic": "nominal",
          "variations": "up_syst,down_syst",
      },
      "dsamuonID_cosmic": {
          "path": f"../tea/DSAMuonSF/id_cosmic/NUM_DisplacedID_DEN_dSAMuons_absdxy.json.gz",
          "type": "NUM_DisplacedID_DEN_dSAMuons_absdxy",
          "systematic": "nominal",
          "variations": "up_syst,down_syst",
      },
      "dsamuonReco_cosmic": {
          "path": f"../tea/DSAMuonSF/reco_cosmic/NUM_RECO_DEN_dSAMuons.json.gz",
          "type": "NUM_RECO_DEN_dSAMuons",
          "systematic": "nominal",
          "variations": "up,down",
      },
  }
  if run2:  # No Run3 PUjetID SF yet
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
    scaleFactors["jecMC"] = {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecType}",
        "level": "L1L2L3Res",
        "algo": f"{jecAlgo}",
        "uncertainties": f"Regrouped_Absolute,Regrouped_Absolute_{jecYear},Regrouped_FlavorQCD,Regrouped_BBEC1,Regrouped_BBEC1_{jecYear},Regrouped_EC2,Regrouped_EC2_{jecYear},Regrouped_HF,Regrouped_HF_{jecYear},Regrouped_RelativeBal,Regrouped_RelativeSample_{jecYear}",
    }
  else:
    # No regrouped JEC uncertainties in jsonPOG for Run 3
    scaleFactors["jecMC"] = {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecType}",
        "level": "L1L2L3Res",
        "algo": f"{jecAlgo}",
        "uncertainties": f"AbsoluteMPFBias,AbsoluteScale,AbsoluteStat,FlavorQCD,Fragmentation,PileUpDataMC,PileUpPtBB,PileUpPtEC1,PileUpPtEC2,PileUpPtHF,PileUpPtRef,RelativeFSR,RelativeJEREC1,RelativeJEREC2,RelativeJERHF,RelativePtBB,RelativePtEC1,RelativePtEC2,RelativePtHF,RelativeBal,RelativeSample,RelativeStatEC,RelativeStatFSR,RelativeStatHF,SinglePionECAL,SinglePionHCAL,TimePtEta",
    }
  return scaleFactors
