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
  try {
    config.GetValue("rhoBranchName", rhoBranchName);
  } catch (const Exception &e) {
    warn() << "rhoBranchName not specified in config -- will assume standard name fixedGridRhoFastjetAll" << endl;
    rhoBranchName = "fixedGridRhoFastjetAll";
  }
  try {
    config.GetValue("eventIDBranchName", eventIDBranchName);
  } catch (const Exception &e) {
    warn() << "eventIDBranchName not specified in config -- will assume standard name event" << endl;
    eventIDBranchName = "event";
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
      UpdateVariationWeights(weights, weights_dsa);
    } else {
      if (muon->IsTight()) {
        auto weights_tight = muon->GetScaleFactors("muonIDTight", "muonIsoTight", "muonReco", year);
        for (auto& [name, weight] : weights_tight) weights[name] *= weight;
        // update all other variations with new systematic
        UpdateVariationWeights(weights, weights_tight);
      } else {
        auto weights_loose = muon->GetScaleFactors("muonIDLoose", "muonIsoLoose", "muonReco", year);
        for (auto& [name, weight] : weights_loose) weights[name] *= weight;
        // update all other variations with new systematic
        UpdateVariationWeights(weights, weights_loose);
      }
    }
  }
  return weights;
}

void NanoEventProcessor::UpdateVariationWeights(map<string, float>& weightsToUpdate, map<string, float>& alreadyUpdatedWeights) {
  for (auto& [name, weight] : weightsToUpdate) {
    if (name == "systematic") {
      continue;
    }
    if (alreadyUpdatedWeights.find(name) != alreadyUpdatedWeights.end())
      continue;
    weightsToUpdate[name] *= alreadyUpdatedWeights["systematic"];
  }
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

  auto [goodJetPtCuts, goodBJetPtCuts] = GetJetPtCuts(event, goodJetsCollectionName, goodBJetsCollectionName);
  if (goodJetPtCuts.first < 0) {
    error() << "Good jet pt cuts not defined - it is needed for jet energy resolution" << endl;
    return make_tuple(jec, met);
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

      UpdateNPassingJetsForPt(newJetPt, name, nPassingGoodJets, nPassingGoodBJets, 
                             goodJetPtCuts, goodBJetPtCuts, isGoodJet, isGoodBJet);
      
      string met_name = name;
      size_t pos = met_name.find("jec");
      if (pos != std::string::npos) {
        met_name.replace(pos, 3, "met"); 
      }
      UpdateMETDifferenceForPt(nanoJet, newJetPt, pt, met_name, totalPxDifference, totalPyDifference);
    }
  }
  UpdateSFsForJetJEC(jec, nPassingGoodJets, nPassingGoodBJets, goodJetCuts, goodBJetCuts);
  UpdateSFsForMETJEC(event, met, totalPxDifference, totalPyDifference, metPtCuts);
  return make_tuple(jec, met);
}

tuple<pair<float, float>,pair<float, float>> NanoEventProcessor::GetJetPtCuts(const shared_ptr<NanoEvent> event, string goodJetsCollectionName, string goodBJetsCollectionName) {
  auto extraCollectionsDescriptions = event->GetEvent()->GetExtraCollectionsDescriptions();
  auto goodJetsPtCutsIt = extraCollectionsDescriptions[goodJetsCollectionName].allCuts.find("pt");
  auto goodBJetsPtCutsIt = extraCollectionsDescriptions[goodBJetsCollectionName].allCuts.find("pt");
  pair<float, float> goodJetPtCuts;
  pair<float, float> goodBJetPtCuts;
  if (goodJetsPtCutsIt != extraCollectionsDescriptions[goodJetsCollectionName].allCuts.end()) {
    goodJetPtCuts = goodJetsPtCutsIt->second;
  } else {
    error() << "Good jet pt cuts not defined - it is needed for jet energy resolution" << endl;
    return make_tuple(make_pair(-1.f, -1.f),make_pair(-1.f, -1.f));
  }
  if (goodBJetsPtCutsIt != extraCollectionsDescriptions[goodBJetsCollectionName].allCuts.end()) {
    goodBJetPtCuts = goodBJetsPtCutsIt->second;
  } else {
    goodBJetPtCuts = goodJetPtCuts;
  }
  return make_tuple(goodJetPtCuts, goodBJetPtCuts);
}

void NanoEventProcessor::UpdateNPassingJetsForPt(float newJetPt, string name,
    map<string,int>& nPassingGoodJets, map<string,int>& nPassingGoodBJets, 
    pair<float, float> goodJetPtCuts, pair<float, float> goodBJetPtCuts,
    bool isGoodJet, bool isGoodBJet) {
  if (nPassingGoodJets.find(name) == nPassingGoodJets.end()) {
    nPassingGoodJets[name] = 0;
    nPassingGoodBJets[name] = 0;
  }
  if (isGoodJet && newJetPt >= goodJetPtCuts.first && newJetPt <= goodJetPtCuts.second) {
    nPassingGoodJets[name]++;
  }
  if (isGoodBJet && newJetPt >= goodBJetPtCuts.first && newJetPt <= goodBJetPtCuts.second) {
    nPassingGoodBJets[name]++;
  }
}

void NanoEventProcessor::UpdateMETDifferenceForPt(const shared_ptr<NanoJet> nanoJet, float newJetPt, float oldJetPt, string name,
    map<string,float>& totalPxDifference, map<string,float>& totalPyDifference) {

  if (totalPxDifference.find(name) == totalPxDifference.end()) {
    totalPxDifference[name] = 0;
    totalPyDifference[name] = 0;
  }
  totalPxDifference[name] += nanoJet->GetPxDifference(newJetPt, oldJetPt);
  totalPyDifference[name] += nanoJet->GetPyDifference(newJetPt, oldJetPt);
}

void NanoEventProcessor::UpdateSFsForJetJEC(map<string, float>& jecSFs, map<string,int> nPassingGoodJets, map<string,int> nPassingGoodBJets,
    pair<float,float> goodJetCuts, pair<float,float> goodBJetCuts) {
  for (auto &[name, nPassingJets] : nPassingGoodJets) {
    jecSFs[name] = 0.0;
    if (nPassingGoodJets[name] < goodJetCuts.first || nPassingGoodJets[name] > goodJetCuts.second) continue;
    if (nPassingGoodBJets[name] < goodBJetCuts.first || nPassingGoodBJets[name] > goodBJetCuts.second) continue;
    jecSFs[name] = 1.0;
  }
}

void NanoEventProcessor::UpdateSFsForMETJEC(const shared_ptr<NanoEvent> event, map<string, float>& metSFs, 
    map<string,float> totalPxDifference, map<string,float> totalPyDifference, pair<float,float> metPtCuts) {
  for (auto &[name, pxDifference] : totalPxDifference) {
    metSFs[name] = 0.0;
    float newMetPt = PropagateMET(event, totalPxDifference[name], totalPyDifference[name]);
    if (newMetPt < metPtCuts.first || newMetPt > metPtCuts.second) continue;
    metSFs[name] = 1.0;
  }
}

void NanoEventProcessor::ApplyJetEnergyResolution(const shared_ptr<NanoEvent> event) {  
  float rho = event->Get(rhoBranchName);
  ULong64_t eventID = event->Get(eventIDBranchName);
  auto jets = event->GetCollection("Jet");
  map<string,float> totalPxDifference, totalPyDifference;
  for (auto jet : *jets) {
    asNanoJet(jet)->AddSmearedPtByResolution(rho, eventID, event);
    float pt_unsmeared = asNanoJet(jet)->GetPt();
    float pt_smeared = jet->Get("pt_smeared");
    UpdateMETDifferenceForPt(asNanoJet(jet), pt_smeared, pt_unsmeared, "met_jer",
                               totalPxDifference, totalPyDifference);
  }
  float newMetPt = PropagateMET(event, totalPxDifference["met_jer"], totalPyDifference["met_jer"]);
  event->GetEvent()->SetFloat("MET_pt_smeared", newMetPt);
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

  auto [goodJetPtCuts, goodBJetPtCuts] = GetJetPtCuts(event, goodJetsCollectionName, goodBJetsCollectionName);
  if (goodJetPtCuts.first < 0) {
    error() << "Good jet pt cuts not defined - it is needed for jet energy resolution" << endl;
    return make_tuple(jer, met);
  }

  auto jets = event->GetCollection(allJetsCollectionName);
  map<string,int> nPassingGoodJets, nPassingGoodBJets;
  map<string,float> totalPxDifference, totalPyDifference;
  vector<string> pt_variation_names = {"up", "down"};
  for (auto jet : *jets) {
    auto nanoJet = asNanoJet(jet);
    float pt_smeared_nom = nanoJet->Get("pt_smeared");

    const bool isGoodJet = nanoJet->IsInCollection(goodJetCollection);
    const bool isGoodBJet = nanoJet->IsInCollection(goodBJetCollection);

    for (auto name : pt_variation_names) {
      float pt_smeared_variation = nanoJet->Get("pt_smeared_" + name);

      UpdateNPassingJetsForPt(pt_smeared_variation, "jer_" + name, nPassingGoodJets, nPassingGoodBJets, 
                             goodJetPtCuts, goodBJetPtCuts, isGoodJet, isGoodBJet);

      UpdateMETDifferenceForPt(nanoJet, pt_smeared_variation, pt_smeared_nom, "met_jer_" + name,
                               totalPxDifference, totalPyDifference);
    }
  }
  UpdateSFsForJetJEC(jer, nPassingGoodJets, nPassingGoodBJets, goodJetCuts, goodBJetCuts);
  UpdateSFsForMETJEC(event, met, totalPxDifference, totalPyDifference, metPtCuts);
  
  return make_tuple(jer,met);
}
