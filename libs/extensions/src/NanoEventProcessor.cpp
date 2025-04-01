//  NanoEventProcessor.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "NanoEventProcessor.hpp"

using namespace std;

NanoEventProcessor::NanoEventProcessor() {
  eventProcessor = make_unique<EventProcessor>();
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetValue("weightsBranchName", weightsBranchName);
  } catch (const Exception &e) {
    warn() << "Weights branch not specified -- will assume weight is 1 for all events" << endl;
  }
  try {
    config.GetValue("year", year);
  } catch (const Exception &e) {
    info() << "Couldn't read year from config file - will assume year 2018" << endl;
    year = "2018";
  }
}

float NanoEventProcessor::GetGenWeight(const std::shared_ptr<NanoEvent> event) {
  float weight = 1.0;
  if (weightsBranchName.empty()) return weight;
  try {
    weight = event->Get(weightsBranchName);
  } catch (const Exception &e) {
    warn() << "NanoEventProcessor failed to get gen weight from branch: " << weightsBranchName << endl;
  }
  return weight;
}

float NanoEventProcessor::GetPileupScaleFactor(const std::shared_ptr<NanoEvent> event, string name) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  if (name == "custom") {
    int nVertices = event->GetAs<int>("PV_npvsGood");
    return scaleFactorsManager.GetPileupScaleFactorCustom(nVertices);
  } else {
    float nVertices = event->Get("Pileup_nTrueInt");
    return scaleFactorsManager.GetPileupScaleFactor(name, nVertices);
  }
}

map<string,float> NanoEventProcessor::GetMuonTriggerScaleFactor(const shared_ptr<NanoEvent> event, string name) {
  map<string,float> weights;
  if (!event->GetMuonTriggerSF().empty()) return event->GetMuonTriggerSF();

  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  auto leadingMuon = asNanoMuon(eventProcessor->GetMaxPtObject(event->GetEvent(), "Muon"));
  if(!leadingMuon) {
    warn() << "No leading muon found in event -- will assume SF=1.0" << endl;
    return weights;
  }
  weights = scaleFactorsManager.GetMuonTriggerScaleFactor(name, leadingMuon->GetEta(), leadingMuon->GetPt());
  event->SetMuonTriggerSF(weights);

  return weights;
}

map<string,float> NanoEventProcessor::GetMediumBTaggingScaleFactors(const shared_ptr<NanoJets> b_jets) {
  map<string,float> weights;
  bool firstIteration = true;
  for (auto b_jet : * b_jets) {
    map<string,float> weights_ = b_jet->GetBtaggingScaleFactor("bTaggingMedium");
    if (firstIteration) {
      weights = weights_;
      firstIteration = false;
      continue;
    }
    for (auto &[name, weight] : weights_) {
      weights[name] *= weight;
    }
  }
  return weights;
}

map<string,float> NanoEventProcessor::GetPUJetIDScaleFactors(const shared_ptr<NanoJets> jets) {
  map<string,float> weights;
  bool firstIteration = true;
  for (auto jet : * jets) {
    map<string,float> weights_ = jet->GetPUJetIDScaleFactor("PUjetIDtight");
    if (firstIteration) {
      weights = weights_;
      firstIteration = false;
      continue;
    }
    for (auto &[name, weight] : weights_) {
      weights[name] *= weight;
    }
  }
  return weights;
}

map<string,float> NanoEventProcessor::GetMuonScaleFactors(const std::shared_ptr<NanoMuons> muonCollection) {
  map<string,float> weights;
  bool firstIteration = true;
  for (auto muon : *muonCollection) {
    auto weights_loose = muon->GetScaleFactor("muonIDLoose", "muonIsoLoose", "muonReco", year);
    auto weights_tight = muon->GetScaleFactor("muonIDTight", "muonIsoTight", "muonReco", year);
    if (firstIteration) {
      if (muon->IsTight()) weights = weights_tight;
      else weights = weights_loose;
      firstIteration = false;
      continue;
    }

    for (auto &[name, weight] : weights_loose) {
      if (muon->IsTight()) weight = 1.0;
      weights[name] *= weight;
    }
    for (auto &[name, weight] : weights_tight) {
      if (!muon->IsTight()) weight = 1.0;
      weights[name] *= weight;
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
      float genWeight = event->Get(weightsBranchName);
    } catch (const Exception &e) {
      isData = true;
    }
  }
  // Test 2: run run = 1 for MC
  int run = event->GetAs<int>("run");
  if (run == 1) {
    if (isData) {
      warn() << "Conflicting NanoEventProcessor::IsDataEvent results. Returning IsDataEvent true";
      return true;
    }
    return false;
  }
  if (!isData) warn() << "Conflicting NanoEventProcessor::IsDataEvent results. Returning IsDataEvent true";
  return true;
}
