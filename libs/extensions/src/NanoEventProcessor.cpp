//  NanoEventProcessor.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "NanoEventProcessor.hpp"

using namespace std;

NanoEventProcessor::NanoEventProcessor() {
  eventProcessor = make_unique<EventProcessor>();
  auto& config = ConfigManager::GetInstance();

  try {
    config.GetValue("weightsBranchName", weightsBranchName);
  } catch (const Exception& e) {
    warn() << "Weights branch not specified in the config file! Will assume 1.0 for all events." << endl;
  }
  try {
    config.GetValue("year", year);
  } catch (const Exception& e) {
    warn() << "Year not found in the config file! Will assume 2018." << endl;
    year = "2018";
  }
  try {
    config.GetCuts(eventCuts);
  } catch (const Exception& e) {
    warn() << "Couldn't read eventCuts from config file " << endl;
  }
}

float NanoEventProcessor::GetGenWeight(const std::shared_ptr<NanoEvent> event) {
  float weight = 1.0;
  if (weightsBranchName.empty()) return weight;
  try {
    weight = event->Get(weightsBranchName);
  } catch (const Exception& e) {
    warn() << "NanoEventProcessor failed to get gen weight from branch: " << weightsBranchName << endl;
  }
  return weight;
}

map<string, float> NanoEventProcessor::GetPileupScaleFactor(const std::shared_ptr<NanoEvent> event, string name) {
  auto& scaleFactorsManager = ScaleFactorsManager::GetInstance();

  // TODO: implement custom pileup scale factor for other years?
  if (year == "2018" && name == "custom") {
    int nVertices = event->GetAs<int>("PV_npvsGood");
    return scaleFactorsManager.GetPileupScaleFactorCustom(nVertices);
  } else {
    float nVertices = event->Get("Pileup_nTrueInt");
    return scaleFactorsManager.GetPileupScaleFactor("pileup", nVertices);
  }
}

map<string, float> NanoEventProcessor::GetL1PreFiringWeight(const std::shared_ptr<NanoEvent> event, string name) {
  map<string, float> weights;

  // L1PreFiringWeight only implemented for Run2 right now
  if (year != "2016preVFP" && year != "2016postVFP" && year != "2017" && year != "2018") {
    warn() << "L1PreFiringWeight only given for Run 2 -- will assume SF=1.0" << endl;
    return {{"systematic", 1.0}};
  }

  auto& config = ConfigManager::GetInstance();

  map<string, vector<bool>> applyScaleFactors;
  config.GetMap("applyScaleFactors", applyScaleFactors);
  if (!applyScaleFactors.count(name)) {
    error() << "L1PreFiringWeight not defined in config/files_config -- will assume SF=1.0" << endl;
    return {{"systematic", 1.0}};
  }

  map<string, map<string, string>> scaleFactors;
  config.GetMap("scaleFactors", scaleFactors);
  if (scaleFactors.find(name) == scaleFactors.end()) {
    warn() << "L1PreFiringWeight not defined in scale_factors_config -- will assume SF=1.0" << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = scaleFactors[name];

  weights["systematic"] = applyScaleFactors[name][0] ? event->Get(name + "_" + extraArgs["systematic"]) : 1.0;

  if (!applyScaleFactors[name][1]) return weights;

  stringstream ss(extraArgs["variations"]);
  string variation;
  while (getline(ss, variation, ',')) {
    weights[name + "_" + variation] = event->Get(name + "_" + variation);
  }

  return weights;
}

map<string, float> NanoEventProcessor::GetMuonTriggerScaleFactors(const shared_ptr<NanoEvent> event, string name) {
  map<string, float> weights;
  if (!event->GetMuonTriggerScaleFactors().empty()) return event->GetMuonTriggerScaleFactors();

  auto& scaleFactorsManager = ScaleFactorsManager::GetInstance();

  auto leadingMuon = asNanoMuon(eventProcessor->GetMaxPtObject(event->GetEvent(), "Muon"));
  if (!leadingMuon) {
    warn() << "No leading muon found in event -- will assume SF=1.0" << endl;
    return {{"systematic", 1.0}};
  }
  weights = scaleFactorsManager.GetMuonTriggerScaleFactors(name, leadingMuon->GetEta(), leadingMuon->GetPt());
  event->SetMuonTriggerScaleFactors(weights);

  return weights;
}

map<string, float> NanoEventProcessor::GetMediumBTaggingScaleFactors(const shared_ptr<NanoJets> b_jets) {
  map<string, float> weights;
  bool firstIteration = true;
  for (auto b_jet : *b_jets) {
    map<string, float> weights_ = b_jet->GetBtaggingScaleFactors("bTaggingMedium");
    if (firstIteration) {
      weights = weights_;
      firstIteration = false;
      continue;
    }
    for (auto& [name, weight] : weights_) {
      weights[name] *= weight;
    }
  }
  // special case for 0 b-jets but we still need all variation names for histograms
  if (b_jets->size() == 0) {
    weights["systematic"] = 1.0;
    auto& scaleFactorsManager = ScaleFactorsManager::GetInstance();
    auto variations = scaleFactorsManager.GetBTagVariationNames("bTaggingMedium");
    for (auto variation : variations) {
      weights["bTaggingMedium_" + variation] = 1.0;
    }
  }
  return weights;
}

map<string, float> NanoEventProcessor::GetPUJetIDScaleFactors(const shared_ptr<NanoJets> jets) {
  map<string, float> weights;
  bool firstIteration = true;
  for (auto jet : *jets) {
    map<string, float> weights_ = jet->GetPUJetIDScaleFactors("PUjetIDtight");
    if (firstIteration) {
      weights = weights_;
      firstIteration = false;
      continue;
    }
    for (auto& [name, weight] : weights_) {
      weights[name] *= weight;
    }
  }
  return weights;
}

map<string, float> NanoEventProcessor::GetMuonScaleFactors(const std::shared_ptr<NanoMuons> muonCollection) {
  map<string, float> weights;
  bool firstIteration = true;
  for (auto muon : *muonCollection) {
    if (firstIteration) {
      auto weights_loose = muon->GetEmptyScaleFactors("muonIDLoose", "muonIsoLoose", "muonReco", year);
      auto weights_tight = muon->GetEmptyScaleFactors("muonIDTight", "muonIsoTight", "muonReco", year);
      auto weights_dsa = muon->GetEmptyDSAScaleFactors("dsamuonID", "dsamuonReco_cosmic");
      for (auto& [name, weight] : weights_loose) {
        weights[name] = 1.0;
      }
      for (auto& [name, weight] : weights_tight) {
        weights[name] = 1.0;
      }
      for (auto& [name, weight] : weights_dsa) {
        weights[name] = 1.0;
      }
      firstIteration = false;
    }

    if (muon->IsDSA()) {
      auto weights_dsa = muon->GetDSAScaleFactors("dsamuonID", "dsamuonReco_cosmic");
      for (auto& [name, weight] : weights_dsa) weights[name] *= weight;
      // update all other variations with new systematic
      for (auto& [name, weight] : weights) {
        if (name == "systematic") {
          continue;
        }
        if (weights_dsa.find(name) != weights_dsa.end())
          continue;
        weights[name] *= weights_dsa["systematic"];
      }
    } else {
      if (muon->IsTight()) {
        auto weights_tight = muon->GetScaleFactors("muonIDTight", "muonIsoTight", "muonReco", year);
        for (auto& [name, weight] : weights_tight) weights[name] *= weight;
        // update all other variations with new systematic
        for (auto& [name, weight] : weights) {
          if (name == "systematic") {
            continue;
          }
          if (weights_tight.find(name) != weights_tight.end())
            continue;
          weights[name] *= weights_tight["systematic"];
        }
      } else {
        auto weights_loose = muon->GetScaleFactors("muonIDLoose", "muonIsoLoose", "muonReco", year);
        for (auto& [name, weight] : weights_loose) weights[name] *= weight;
        // update all other variations with new systematic
        for (auto& [name, weight] : weights) {
          if (name == "systematic") {
            continue;
          }
          if (weights_loose.find(name) != weights_loose.end())
            continue;
          weights[name] *= weights_loose["systematic"];
        }
      }
    }
  }
  return weights;
}

map<string, float> NanoEventProcessor::GetDSAMuonEfficiencyScaleFactors(const shared_ptr<NanoMuons> muonCollection) {
  map<string, float> weights;
  auto& scaleFactorsManager = ScaleFactorsManager::GetInstance();
  bool firstIteration = true;
  for (auto muon : *muonCollection) {
    vector<variant<int, double, string>> args = {double(muon->Get("pt"))};
    // vector<variant<int, double, string>> args = {double(muon->Get("pt")), double(fabs(muon->GetAs<float>("dxyPVTraj")))};
    if (firstIteration) {
      auto weights_setup = scaleFactorsManager.GetCustomScaleFactors("DSAEff", args);
      for (auto& [name, weight] : weights_setup) weights[name] = 1.0;
      firstIteration = false;
    }

    if (!muon->IsDSA()) {
      continue;
    }
    auto weights_ = scaleFactorsManager.GetCustomScaleFactors("DSAEff", args);
    for (auto& [name, weight] : weights_) weights[name] *= weight;
  }
  float systematic = weights["systematic"];
  for (auto& [name, weight] : weights) {
    if (weight == 1.0) {
      weights[name] = systematic;
    }
  }
  return weights;
}

pair<shared_ptr<NanoMuon>, shared_ptr<NanoMuon>> NanoEventProcessor::GetMuonPairClosestToZ(const std::shared_ptr<NanoEvent> event,
                                                                                           string collection) {
  auto muons = event->GetCollection(collection);
  if (muons->size() < 2) return {nullptr, nullptr};

  shared_ptr<NanoMuon> muonA;
  shared_ptr<NanoMuon> muonB;

  double zMass = 91.1876;  // GeV
  double smallestDifferenceToZmass = 999999;
  double massClosestToZ = -1;

  for (int iMuon1 = 0; iMuon1 < muons->size(); iMuon1++) {
    auto muon1 = asNanoMuon(muons->at(iMuon1));
    auto muon1fourVector = muon1->GetFourVector();

    for (int iMuon2 = iMuon1 + 1; iMuon2 < muons->size(); iMuon2++) {
      auto muon2 = asNanoMuon(muons->at(iMuon2));
      auto muon2fourVector = muon2->GetFourVector();

      double diMuonMass = (muon1fourVector + muon2fourVector).M();
      if (fabs(diMuonMass - zMass) < smallestDifferenceToZmass) {
        smallestDifferenceToZmass = fabs(diMuonMass - zMass);
        muonA = muon1;
        muonB = muon2;
      }
    }
  }

  return {muonA, muonB};
}

bool NanoEventProcessor::IsDataEvent(const std::shared_ptr<NanoEvent> event) {
  // Test 1: gen wights branch only for MC
  bool isData = false;
  if (!weightsBranchName.empty()) {
    try {
      event->Get(weightsBranchName);
    } catch (const Exception& e) {
      isData = true;
    }
  }
  // Test 2: run run = 1 for MC
  unsigned run = event->Get("run");
  if (run == 1) {
    if (isData) {
      fatal() << "Conflicting NanoEventProcessor::IsDataEvent results.";
      exit(1);
    }
    return false;
  }
  if (!isData) {
    fatal() << "Conflicting NanoEventProcessor::IsDataEvent results.";
    exit(1);
  }
  return true;
}

float NanoEventProcessor::PropagateMET(const shared_ptr<NanoEvent> event, float totalPxDifference, float totalPyDifference) {
  float metPt = event->Get("MET_pt");
  float metPhi = event->Get("MET_phi");
  float newMetPx = metPt * cos(metPhi) - totalPxDifference;
  float newMetPy = metPt * sin(metPhi) - totalPyDifference;
  return sqrt(newMetPx * newMetPx + newMetPy * newMetPy);
}

bool NanoEventProcessor::PassesEventCuts(const shared_ptr<NanoEvent> event, shared_ptr<CutFlowManager> cutFlowManager) {
  if (!eventProcessor->PassesEventCuts(event->GetEvent(), cutFlowManager)) return false;

  for (auto& [cutName, cutValues] : eventCuts) {
    if (cutName.substr(0, 5) != "nano_") continue;

    if (cutName == "nano_applyHEMveto") {
      if (cutValues.first > 0.5 && !event->PassesHEMveto(cutValues.second)) return false;
    } else if (cutName == "nano_applyJetVetoMaps") {
      if (cutValues.first > 0.5 && !event->PassesJetVetoMaps()) return false;
    } else {
      error() << "Unknown nano event cut: " << cutName << endl;
      continue;
    }

    if (cutFlowManager) cutFlowManager->UpdateCutFlow(cutName);
  }

  return true;
}

tuple<map<string, float>,map<string, float>> NanoEventProcessor::GetJetMETEnergyScaleUncertainties(shared_ptr<NanoEvent> event,
    string allJetsCollectionName, string goodJetsCollectionName, string goodBJetsCollectionName,
    pair<float,float> goodJetCuts, pair<float,float> goodBJetCuts, pair<float,float> metPtCuts) {
  
  map<string, float> jec = {{"systematic", 1.0}};
  map<string, float> met = {{"systematic", 1.0}};

  auto baseJetCollection = event->GetCollection(allJetsCollectionName);
  auto goodJetCollection = event->GetCollection(goodJetsCollectionName);
  auto goodBJetCollection = event->GetCollection(goodBJetsCollectionName);

  auto extraCollectionsDescriptions = event->GetEvent()->GetExtraCollectionsDescriptions();
  auto goodJetsPtCutsIt = extraCollectionsDescriptions[goodJetsCollectionName].allCuts.find("pt");
  auto goodBJetsPtCutsIt = extraCollectionsDescriptions[goodBJetsCollectionName].allCuts.find("pt");
  pair<float, float> goodJetPtCuts;
  pair<float, float> goodBJetPtCuts;
  if (goodJetsPtCutsIt != extraCollectionsDescriptions[goodJetsCollectionName].allCuts.end()) {
    goodJetPtCuts = goodJetsPtCutsIt->second;
  } else {
    error() << "Good jet pt cuts not defined - it is needed for jet energy corrections" << endl;
    return make_tuple(jec, met);
  }
  if (goodBJetsPtCutsIt != extraCollectionsDescriptions[goodBJetsCollectionName].allCuts.end()) {
    goodBJetPtCuts = goodBJetsPtCutsIt->second;
  } else {
    goodBJetPtCuts = goodJetPtCuts;
  }

  auto &config = ConfigManager::GetInstance();
  string rhoBranchName;
  try {
    config.GetValue("rhoBranchName", rhoBranchName);
  } catch (const Exception &e) {
    warn() << "Rho branch not specified -- will assume standard name fixedGridRhoFastjetAll" << endl;
    rhoBranchName = "fixedGridRhoFastjetAll";
  }
  float rho = event->Get(rhoBranchName);
  
  map<string,int> nPassingGoodJets, nPassingGoodBJets;
  map<string,float> totalPxDifference, totalPyDifference;
  for (auto jet : *baseJetCollection) {
    auto nanoJet = asNanoJet(jet);
    map<string,float> corrections = nanoJet->GetJetEnergyCorrections(rho);
    float pt = nanoJet->GetPt();

    const bool isGoodJet = nanoJet->IsInCollection(goodJetCollection);
    const bool isGoodBJet = nanoJet->IsInCollection(goodBJetCollection);
    
    for (auto &[name, correction] : corrections) {
      float newJetPt = pt*correction;

      if (nPassingGoodJets.find(name) == nPassingGoodJets.end()) {
        nPassingGoodJets[name] = 0;
        nPassingGoodBJets[name] = 0;
        totalPxDifference[name] = 0;
        totalPyDifference[name] = 0;
      }

      if (isGoodJet && newJetPt >= goodJetPtCuts.first && newJetPt <= goodJetPtCuts.second) {
        nPassingGoodJets[name]++;
      }
      if (isGoodBJet && newJetPt >= goodBJetPtCuts.first && newJetPt <= goodBJetPtCuts.second) {
        nPassingGoodBJets[name]++;
      }
      // Needed to propagate MET
      totalPxDifference[name] += nanoJet->GetPxDifference(newJetPt);
      totalPyDifference[name] += nanoJet->GetPyDifference(newJetPt);
    }
  }
  for (auto &[name, nPassingJets] : nPassingGoodJets) {
    jec[name] = 0.0;
    if (nPassingGoodJets[name] < goodJetCuts.first || nPassingGoodJets[name] > goodJetCuts.second) continue;
    if (nPassingGoodBJets[name] < goodBJetCuts.first || nPassingGoodBJets[name] > goodBJetCuts.second) continue;
    jec[name] = 1.0;
  }
  for (auto &[name, pxDifference] : totalPxDifference) {
    string met_name = name;
    size_t pos = met_name.find("jec");
    if (pos != std::string::npos) {
      met_name.replace(pos, 3, "met"); 
    }
    met[met_name] = 0.0;
    float newMetPt = PropagateMET(event, totalPxDifference[name], totalPyDifference[name]);
    if (newMetPt < metPtCuts.first || newMetPt > metPtCuts.second) continue;
    met[met_name] = 1.0;
  }
  return make_tuple(jec, met);
}

void NanoEventProcessor::ApplyJetEnergyResolution(const shared_ptr<NanoEvent> event) {
  auto &config = ConfigManager::GetInstance();
  string rhoBranchName, eventIDBranchName;
  try {
    config.GetValue("rhoBranchName", rhoBranchName);
  } catch (const Exception &e) {
    warn() << "Rho branch not specified -- will assume standard name fixedGridRhoFastjetAll" << endl;
    rhoBranchName = "fixedGridRhoFastjetAll";
  }
  try {
    config.GetValue("eventIDBranchName", eventIDBranchName);
  } catch (const Exception &e) {
    warn() << "Event ID branch not specified -- will assume standard name event" << endl;
    eventIDBranchName = "event";
  }
  float rho = event->Get(rhoBranchName);
  ULong64_t eventID_64 = event->Get(eventIDBranchName);
  int eventID = static_cast<int>(eventID_64);
  auto jets = event->GetCollection("Jet");
  for (auto jet : *jets) {
    asNanoJet(jet)->AddJetResolutionPt(rho, eventID, event);
  }
}

tuple<map<string, float>,map<string, float>> NanoEventProcessor::GetJetMETEnergyResolutionUncertainties(const shared_ptr<NanoEvent> event, 
    string allJetsCollectionName, string goodJetsCollectionName, string goodBJetsCollectionName,
    pair<float,float> goodJetCuts, pair<float,float> goodBJetCuts, pair<float,float> metPtCuts) {
  
  auto& scaleFactorsManager = ScaleFactorsManager::GetInstance();
  map<string, float> jer = {{"systematic", 1.0}, {"jer_up", 1.0}, {"jer_down", 1.0}};
  map<string, float> met = {{"systematic", 1.0}, {"met_jer_up", 1.0}, {"met_jer_down", 1.0}};
  if (!scaleFactorsManager.ShouldApplyScaleFactor("jer") && !scaleFactorsManager.ShouldApplyVariation("jer")) 
    return make_tuple(jer, met);

  auto goodJetCollection = event->GetCollection(goodJetsCollectionName);
  auto goodBJetCollection = event->GetCollection(goodBJetsCollectionName);
  auto extraCollectionsDescriptions = event->GetEvent()->GetExtraCollectionsDescriptions();
  auto goodJetsPtCutsIt = extraCollectionsDescriptions[goodJetsCollectionName].allCuts.find("pt");
  auto goodBJetsPtCutsIt = extraCollectionsDescriptions[goodBJetsCollectionName].allCuts.find("pt");
  pair<float, float> goodJetPtCuts;
  pair<float, float> goodBJetPtCuts;
  if (goodJetsPtCutsIt != extraCollectionsDescriptions[goodJetsCollectionName].allCuts.end()) {
    goodJetPtCuts = goodJetsPtCutsIt->second;
  } else {
    error() << "Good jet pt cuts not defined - it is needed for jet energy resolution" << endl;
    return make_tuple(jer, met);
  }
  if (goodBJetsPtCutsIt != extraCollectionsDescriptions[goodBJetsCollectionName].allCuts.end()) {
    goodBJetPtCuts = goodBJetsPtCutsIt->second;
  } else{
    goodBJetPtCuts = goodJetPtCuts;
  }

  auto jets = event->GetCollection(allJetsCollectionName);
  float totalPxDifference_up(0.0), totalPyDifference_up(0.0);
  float totalPxDifference_down(0.0), totalPyDifference_down(0.0);
  int nPassingGoodJets_up(0), nPassingGoodJets_down(0);
  int nPassingGoodBJets_up(0), nPassingGoodBJets_down(0);
  for (auto jet : *jets) {
    auto nanoJet = asNanoJet(jet);
    float pt_smeared = nanoJet->Get("pt_smeared");
    float pt_smeared_up = nanoJet->Get("pt_smeared_up");
    float pt_smeared_down = nanoJet->Get("pt_smeared_down");
    totalPxDifference_up += nanoJet->GetPxDifference(pt_smeared_up, pt_smeared);
    totalPyDifference_up += nanoJet->GetPyDifference(pt_smeared_up, pt_smeared);
    totalPxDifference_down += nanoJet->GetPxDifference(pt_smeared_down, pt_smeared);
    totalPyDifference_down += nanoJet->GetPyDifference(pt_smeared_down, pt_smeared);
    
    const bool isGoodJet = nanoJet->IsInCollection(goodJetCollection);
    const bool isGoodBJet = nanoJet->IsInCollection(goodBJetCollection);
    if (isGoodJet && pt_smeared_up >= goodJetPtCuts.first && pt_smeared_up <= goodJetPtCuts.second) {
      nPassingGoodJets_up++;
    }
    if (isGoodJet && pt_smeared_down >= goodJetPtCuts.first && pt_smeared_down <= goodJetPtCuts.second) {
      nPassingGoodJets_down++;
    }
    if (isGoodBJet && pt_smeared_up >= goodBJetPtCuts.first && pt_smeared_up <= goodBJetPtCuts.second) {
      nPassingGoodBJets_up++;
    }
    if (isGoodBJet && pt_smeared_down >= goodBJetPtCuts.first && pt_smeared_down <= goodBJetPtCuts.second) {
      nPassingGoodBJets_down++;
    }
  }

  if (nPassingGoodJets_up < goodJetCuts.first || nPassingGoodJets_up > goodJetCuts.second)
    jer["jer_up"] = 0.0;
  if (nPassingGoodJets_down < goodJetCuts.first || nPassingGoodJets_down > goodJetCuts.second)
    jer["jer_down"] = 0.0;
  if (nPassingGoodBJets_up < goodBJetCuts.first || nPassingGoodBJets_up > goodBJetCuts.second)
    jer["jer_up"] = 0.0;
  if (nPassingGoodBJets_down < goodBJetCuts.first || nPassingGoodBJets_down > goodBJetCuts.second)
    jer["jer_down"] = 0.0;

  float newMetPt_up = PropagateMET(event, totalPxDifference_up, totalPyDifference_up);
  float newMetPt_down = PropagateMET(event, totalPxDifference_down, totalPyDifference_down);
  if (newMetPt_up < metPtCuts.first || newMetPt_up > metPtCuts.second) met["met_jer_up"] = 0.0;
  if (newMetPt_down < metPtCuts.first || newMetPt_down > metPtCuts.second) met["met_jer_down"] = 0.0;
  return make_tuple(jer,met);
}
