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

float NanoEventProcessor::GetMuonTriggerScaleFactor(const shared_ptr<NanoEvent> event, string name) {
  if (event->GetMuonTriggerSF() > 0) return event->GetMuonTriggerSF();

  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  auto leadingMuon = asNanoMuon(eventProcessor->GetMaxPtObject(event->GetEvent(), "Muon"));
  if(!leadingMuon) {
    warn() << "No leading muon found in event -- will assume SF=1.0" << endl;
    return 1.0;
  }
  float scaleFactor = scaleFactorsManager.GetMuonTriggerScaleFactor(name, leadingMuon->GetEta(), leadingMuon->GetPt());
  event->SetMuonTriggerSF(scaleFactor);

  return scaleFactor;
}

map<string,float> NanoEventProcessor::GetMediumBTaggingScaleFactors(const shared_ptr<NanoJets> b_jets) {
  map<string,float> weights;
  weights["central"] = 1.0;
  weights["upCorrelated"] = 1.0;
  weights["downCorrelated"] = 1.0;
  weights["upUncorrelated"] = 1.0;
  weights["downUncorrelated"] = 1.0;
  for (auto b_jet : * b_jets) {
    weights["central"] *= b_jet->GetBtaggingScaleFactor("bTaggingMedium");
    weights["upCorrelated"] *= b_jet->GetBtaggingScaleFactor("bTaggingMedium", "systematicUpCorrelated");
    weights["downCorrelated"] *= b_jet->GetBtaggingScaleFactor("bTaggingMedium", "systematicDownCorrelated");
    weights["upUncorrelated"] *= b_jet->GetBtaggingScaleFactor("bTaggingMedium", "systematicUpUncorrelated");
    weights["downUncorrelated"] *= b_jet->GetBtaggingScaleFactor("bTaggingMedium", "systematicDownUncorrelated");
  }
  return weights;
}

map<string,float> NanoEventProcessor::GetPUJetIDScaleFactors(const shared_ptr<NanoJets> jets) {
  map<string,float> weights;
  weights["central"] = 1.0;
  weights["up"] = 1.0;
  weights["down"] = 1.0;
  for (auto jet : * jets) {
    weights["central"] *= jet->GetPUJetIDScaleFactor("PUjetIDtight");
    weights["central"] *= jet->GetPUJetIDScaleFactor("PUjetIDtight", "systematicUp");
    weights["central"] *= jet->GetPUJetIDScaleFactor("PUjetIDtight", "systematicDown");
  }
  return weights;
}

map<string,float> NanoEventProcessor::GetMuonScaleFactors(const std::shared_ptr<NanoMuons> muonCollection) {
  float weight = 1.0;
  for (auto muon : *muonCollection) {
    if (muon->isTight()) weight *= muon->GetScaleFactor("muonIDTight", "muonIsoTight", "muonReco", year);
    else weight *= muon->GetScaleFactor("muonIDLoose", "muonIsoLoose", "muonReco", year);
  }
  map<string,float> weights;
  weights["central"] = weight;
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