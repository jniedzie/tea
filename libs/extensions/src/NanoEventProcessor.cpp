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

float NanoEventProcessor::GetGenWeight(const std::shared_ptr<Event> event) {
  float weight = 1.0;
  try {
    weight = event->Get(weightsBranchName);
  } catch (const Exception &e) {
    warn() << "Coudn't get weight from branch: " << weightsBranchName << endl;
  }
  return weight;
}

float NanoEventProcessor::GetPileupScaleFactor(const std::shared_ptr<Event> event) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  int nVertices = event->Get("PV_npvsGood");
  float pileupSF = scaleFactorsManager.GetPileupScaleFactor(nVertices);

  return pileupSF;
}

float NanoEventProcessor::GetMuonTriggerScaleFactor(const shared_ptr<Event> event, string id, string iso, string triggers) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  auto leadingMuon = asMuon(eventProcessor->GetMaxPtObject(event, "Muon"));
  float scaleFactor = scaleFactorsManager.GetMuonTriggerScaleFactor(leadingMuon->GetEta(), leadingMuon->GetPt(), id, iso, triggers);

  return scaleFactor;
}

pair<shared_ptr<Muon>, shared_ptr<Muon>> NanoEventProcessor::GetMuonPairClosestToZ(const std::shared_ptr<Event> event, string collection) {
  auto muons = event->GetCollection(collection);
  if(muons->size() < 2) return {nullptr, nullptr};

  shared_ptr<Muon> muonA;
  shared_ptr<Muon> muonB;

  double zMass = 91.1876;  // GeV
  double smallestDifferenceToZmass = 999999;
  double massClosestToZ = -1;
  
  for (int iMuon1 = 0; iMuon1 < muons->size(); iMuon1++) {
    auto muon1 = asMuon(muons->at(iMuon1));
    auto muon1fourVector = muon1->GetFourVector();
    
    for (int iMuon2 = iMuon1 + 1; iMuon2 < muons->size(); iMuon2++) {
      auto muon2 = asMuon(muons->at(iMuon2));
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