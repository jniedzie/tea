from ScaleFactorsReader import ScaleFactorsReader
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
