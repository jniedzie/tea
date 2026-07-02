
from Logger import error

jec_mc_types = {
  "2016preVFP": "Summer19UL16APV_V7_MC",
  "2016postVFP": "Summer19UL16_V7_MC",
  "2017": "Summer19UL17_V5_MC",
  "2018": "Summer19UL18_V5_MC",
  "2022preEE": "Summer22_22Sep2023_V2_MC",
  "2022postEE": "Summer22EE_22Sep2023_V2_MC",
  "2023preBPix": "Summer23Prompt23_V2_MC",
  "2023postBPix": "Summer23BPixPrompt23_V3_MC",
}

jec_data_types = {
  "2016preVFP": "Summer19UL16APV_RunBCD_V7_DATA",
  "2016postVFP": "Summer19UL16_RunFGH_V7_DATA",
  "2017": "Summer19UL17_RunB_V5_DATA",
  "2018": "Summer19UL18_RunA_V5_DATA",
  "2022preEE": "Summer22_22Sep2023_RunCD_V2_DATA",
  "2022postEE": "Summer22EE_22Sep2023_RunE_V2_DATA",
  "2023preBPix": "Summer23Prompt23_V2_DATA",
  "2023postBPix": "Summer23BPixPrompt23_V3_DATA",
}

jer_types = {
  "2016preVFP": "Summer20UL16APV_JRV3_MC",
  "2016postVFP": "Summer20UL16_JRV3_MC",
  "2017": "Summer19UL17_JRV2_MC",
  "2018": "Summer19UL18_JRV2_MC",
  "2022preEE": "Summer22_22Sep2023_JRV1_MC",
  "2022postEE": "Summer22EE_22Sep2023_JRV1_MC",
  "2023preBPix": "Summer23Prompt23_RunCv123_JRV1_MC",
  "2023postBPix": "Summer23BPixPrompt23_RunD_JRV1_MC",
}

def get_scale_factors(year, isData=False):
  run2 = True
  if year == "2016preVFP" or year == "2016postVFP":
    pu_type = "Collisions16_UltraLegacy_goldenJSON"
    muon_trigger_type = "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    jecYear = "2016"
    dsaYear = "2016"
  elif year == "2017":
    pu_type = "Collisions17_UltraLegacy_goldenJSON"
    jecYear = "2017"
    dsaYear = "2017"
    muon_trigger_type = "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight"
  elif year == "2018":
    pu_type = "Collisions18_UltraLegacy_goldenJSON"
    jecYear = "2018"
    dsaYear = "2018"
    muon_trigger_type = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
  elif year == "2022preEE" or year == "2022postEE":
    run2 = False
    muon_trigger_type = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    dsaYear = "2022"
    if year == "2022preEE":
      year_path = "2022_Summer22"
      pu_type = "Collisions2022_355100_357900_eraBCD_GoldenJson"
      jecYear = "2022"
    if year == "2022postEE":
      year_path = "2022_Summer22EE"
      pu_type = "Collisions2022_359022_362760_eraEFG_GoldenJson"
      jecYear = "2022EE"
  elif year == "2023preBPix" or year == "2023postBPix":
    run2 = False
    muon_trigger_type = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    dsaYear = "2023"
    if year == "2023preBPix":
      year_path = "2023_Summer23"
      pu_type = "Collisions2023_366403_369802_eraBC_GoldenJson"
      jecYear = "2023"
    if year == "2023postBPix":
      year_path = "2023_Summer23BPix"
      pu_type = "Collisions2023_369803_370790_eraD_GoldenJson"
      jecYear = "2023BPix"
  else:
    error(f"Year {year} not supported.")

  jecTypeMC = jec_mc_types[year]
  jecTypeData = jec_data_types[year]
  jerType = jer_types[year]

  if run2:
    year_path = f"{year}_UL"
    loose_muon_iso_type = "NUM_LooseRelIso_DEN_LooseID"
    tight_muon_iso_type = "NUM_TightRelIso_DEN_TightIDandIPCut"
    qjet_type = "deepJet_incl"
    jecAlgo = "AK4PFchs"
  else:
    loose_muon_iso_type = "NUM_LoosePFIso_DEN_LooseID"
    tight_muon_iso_type = "NUM_TightPFIso_DEN_TightID"
    qjet_type = "deepJet_light"
    jecAlgo = "AK4PFPuppi"

  scaleFactors = {

      # b-tagging
      # systematic options: "central", "up/down_correlated" or "up/down_uncorrelated"
      "bTaggingMedium": {
          "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
          "type": "deepJet_mujets",
          "systematic": "central",
          "variations": "up_correlated,down_correlated,up_uncorrelated,down_uncorrelated",
          "workingPoint": "M",
          "flavour": "5", # 5 = b
      },
      "bTaggingTight": {
          "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
          "type": "deepJet_mujets",
          "systematic": "central",
          "variations": "up_correlated,down_correlated,up_uncorrelated,down_uncorrelated",
          "workingPoint": "T",
          "flavour": "5", # 5 = b
      },
      "bTaggingEfficiency": {
        "path": f"../tea/data/b_tagging/jet_efficiency_maps/{year}_jetTagging_efficiency.json.gz",
        "type": "efficiency_B",
        "flavour": "5",
      },
      "cTaggingEfficiency": {
        "path": f"../tea/data/b_tagging/jet_efficiency_maps/{year}_jetTagging_efficiency.json.gz",
        "type": "efficiency_C",
        "flavour": "4",
      },
      "qTaggingEfficiency": {
        "path": f"../tea/data/b_tagging/jet_efficiency_maps/{year}_jetTagging_efficiency.json.gz",
        "type": "efficiency_Q",
        "flavour": "0",
      },

      "bTaggingMedium_cjet": { 
          "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
          "type": "deepJet_comb",
          "systematic": "central",
          "variations": "up_correlated,down_correlated,up_uncorrelated,down_uncorrelated",
          "workingPoint": "M",
          "flavour": "4", # 4 = c
      },
      "bTaggingMedium_qjet": { 
          "path": f"../tea/jsonPOG/POG/BTV/{year_path}/btagging.json.gz",
          "type": qjet_type,
          "systematic": "central",
          "variations": "up_correlated,down_correlated,up_uncorrelated,down_uncorrelated",
          "workingPoint": "M",
          "flavour": "0", # 0 = udsg
      },

      # Muon ID
      "muonIDLoose": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": "NUM_LooseID_DEN_TrackerMuons",
          "systematic": "nominal",
          "variations": "systup,systdown",
          "statistical": "stat",
      },
      "muonIDMedium": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": "NUM_MediumID_DEN_TrackerMuons",
          "systematic": "nominal",
          "variations": "systup,systdown",
          "statistical": "stat",
      },
      "muonIDTight": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": "NUM_TightID_DEN_TrackerMuons",
          "systematic": "nominal",
          "variations": "systup,systdown",
          "statistical": "stat",
      },

      # Muon Iso
      "muonIsoLoose": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": loose_muon_iso_type,
          "systematic": "nominal",
          "variations": "systup,systdown",
          "statistical": "stat",
      },
      "muonIsoTight": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": tight_muon_iso_type,
          "systematic": "nominal",
          "variations": "systup,systdown",
          "statistical": "stat",
      },

      # Pileup
      "pileup": {
          "path": f"../tea/jsonPOG/POG/LUM/{year_path}/puWeights.json.gz",
          "type": f"{pu_type}",
          "systematic": "nominal",
          "variations": "up,down",
      },

      "dimuonEff_Pat": {
          "path": f"../tea/data/dimuonEffSFs/dimuonEffSFs{year}_Pat_pt_irr_v3.json", 
          "type": "dimuonEff_Pat",
          "systematic": "nominal",
          "variations": "up,down",
      },
      "dimuonEff_PatDSA": {
          "path": f"../tea/data/dimuonEffSFs/dimuonEffSFs{year}_PatDSA_pt_irr_v3.json", 
          "type": "dimuonEff_PatDSA",
          "systematic": "nominal",
          "variations": "up,down",
      },
      "dimuonEff_DSA": {
          "path": f"../tea/data/dimuonEffSFs/dimuonEffSFs{year}_DSA_pt_irr_v3.json", 
          "type": "dimuonEff_DSA",
          "systematic": "nominal",
          "variations": "up,down",
      },

      # Muon trigger
      "muonTrigger": {
          "path": f"../tea/jsonPOG/POG/MUO/{year_path}/muon_Z.json.gz",
          "type": muon_trigger_type,
          "systematic": "nominal",
          "variations": "systup,systdown",
          "statistical": "stat",
      },

      # DSA Muon SFs
      "dsamuonID": {
          "path": f"../tea/DSAMuonSF/{dsaYear}_Jpsi/NUM_DisplacedID_DEN_dSAMuons_abseta_pt_schemaV2.json.gz",
          "type": "NUM_DisplacedID_DEN_dSAMuons",
          "systematic": "nominal",
          "variations": "up_syst,down_syst",
      },
      "dsamuonID_cosmic": {
          "path": "../tea/DSAMuonSF/id_cosmic/NUM_DisplacedID_DEN_dSAMuons_absdxy.json.gz",
          "type": "NUM_DisplacedID_DEN_dSAMuons_absdxy",
          "systematic": "nominal",
          "variations": "up_syst,down_syst",
      },
      "dsamuonReco_cosmic": {
          "path": "../tea/DSAMuonSF/reco_cosmic/NUM_RECO_DEN_dSAMuons.json.gz",
          "type": "NUM_RECO_DEN_dSAMuons",
          "systematic": "nominal",
          "variations": "up,down",
      },

      # L1 Pre-firing weights
      "L1PreFiringWeight": {
          "systematic": "Nom",
          "variations": "Up,Dn",
      },

      # Jet veto maps (only apply to Run 3)
      "jetVetoMaps_2022preEE": {
          "path": "../tea/jsonPOG/POG/JME/2022_Summer22/jetvetomaps.json.gz",
          "type": "Summer22_23Sep2023_RunCD_V1",
      },
      "jetVetoMaps_2022postEE": {
          "path": "../tea/jsonPOG/POG/JME/2022_Summer22EE/jetvetomaps.json.gz",
          "type": "Summer22EE_23Sep2023_RunEFG_V1",
      },
      "jetVetoMaps_2023preBPix": {
          "path": "../tea/jsonPOG/POG/JME/2023_Summer23/jetvetomaps.json.gz",
          "type": "Summer23Prompt23_RunC_V1",
      },
      "jetVetoMaps_2023postBPix": {
          "path": "../tea/jsonPOG/POG/JME/2023_Summer23BPix/jetvetomaps.json.gz",
          "type": "Summer23BPixPrompt23_RunD_V1",
      },

      # Jet Energy Correction uncertainties
      "jecMC": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeMC}",
        "level": "L1L2L3Res",
        "algo": f"{jecAlgo}",
        "uncertainties": f"Regrouped_Absolute,Regrouped_Absolute_{jecYear},Regrouped_FlavorQCD,Regrouped_BBEC1,Regrouped_BBEC1_{jecYear},Regrouped_EC2,Regrouped_EC2_{jecYear},Regrouped_HF,Regrouped_HF_{jecYear},Regrouped_RelativeBal,Regrouped_RelativeSample_{jecYear}",
      },

      "jecL1L2L3MC": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeMC}",
        "level": "L1L2L3Res",
        "algo": f"{jecAlgo}",
      },
      "jecL1L2L3Data": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeData}",
        "level": "L1L2L3Res",
        "algo": f"{jecAlgo}",
      },

      "jecL1MC": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeMC}",
        "level": "L1FastJet",
        "algo": f"{jecAlgo}",
      },
      "jecL1Data": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeData}",
        "level": "L1FastJet",
        "algo": f"{jecAlgo}",
      },

      "jecL2MC": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeMC}",
        "level": "L2Relative",
        "algo": f"{jecAlgo}",
      },
      "jecL2Data": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeData}",
        "level": "L2Relative",
        "algo": f"{jecAlgo}",
      },

      "jecL2L3MC": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeMC}",
        "level": "L2L3Residual",
        "algo": f"{jecAlgo}",
      },
      "jecL2L3Data": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jecTypeData}",
        "level": "L2L3Residual",
        "algo": f"{jecAlgo}",
      },

      # Jet Energy Resolution variables
      "jerMC_ScaleFactor": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jerType}_ScaleFactor_{jecAlgo}",
        "systematic": "nom",
        "variations": "up,down",
        "year": year_path,
      },
      "jerMC_PtResolution": {
        "path": f"../tea/jsonPOG/POG/JME/{year_path}/jet_jerc.json.gz",
        "type": f"{jerType}_PtResolution_{jecAlgo}",
        "year": year_path,
      },
      "jerMC_smear": {
        "path": f"../tea/jsonPOG/POG/JME/jer_smear.json.gz",
        "type": "JERSmear",
        "systematic": "nom",
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
        "statistical": "stat",
    }
  return scaleFactors
