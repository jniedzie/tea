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