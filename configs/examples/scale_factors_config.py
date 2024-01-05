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

bTaggingSFsURL = "https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/blob/master/POG/BTV/2018_UL/btagging.json.gz"
bTaggingSFsPath = "../tea/data/b_tagging/btagging.json.gz"

if not os.path.exists(bTaggingSFsPath):  
  info(f"Downloading b-tagging SFs from URL: {bTaggingSFsURL}")
  urllib.request.urlretrieve(bTaggingSFsURL, bTaggingSFsPath)
  
  # print("Unzipping b-tagging SFs...")
  # with gzip.open(bTaggingSFsPath, "rb") as f_in:
  #   with open(bTaggingSFsPath.replace(".gz", ""), "wb") as f_out:
  #     f_out.write(f_in.read())
  # print("Done.")