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
    } else {
      if (muon->IsTight()) {
        auto weights_tight = muon->GetScaleFactors("muonIDTight", "muonIsoTight", "muonReco", year);
        for (auto& [name, weight] : weights_tight) weights[name] *= weight;
      } else {
        auto weights_loose = muon->GetScaleFactors("muonIDLoose", "muonIsoLoose", "muonReco", year);
        for (auto& [name, weight] : weights_loose) weights[name] *= weight;
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
      exit(0);
    }
    return false;
  }
  if (!isData) {
    fatal() << "Conflicting NanoEventProcessor::IsDataEvent results.";
    exit(0);
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
