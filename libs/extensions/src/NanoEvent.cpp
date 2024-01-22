#include "NanoEvent.hpp"

#include "ExtensionsHelpers.hpp"

using namespace std;

TLorentzVector NanoEvent::GetMetFourVector() {
  TLorentzVector metVector;
  metVector.SetPtEtaPhiM(Get("MET_pt"), 0, Get("MET_phi"), 0);
  return metVector;
}

float NanoEvent::GetMetPt() { return Get("MET_pt"); }

shared_ptr<PhysicsObjects> NanoEvent::GetAllMuons(float matchingDeltaR)
{

  auto looseMuons = GetCollection("LooseMuons");
  auto looseDsaMuons = GetCollection("LooseDSAMuons");

  auto allMuons = make_shared<PhysicsObjects>();
  for(auto muon : *looseMuons){
    auto muonP4 = asNanoMuon(muon)->GetFourVector();
  
    allMuons->push_back(muon);
    for(auto dsaMuon : *looseDsaMuons){
      auto dsaMuonP4 = asNanoMuon(dsaMuon)->GetFourVector();
      if(muonP4.DeltaR(dsaMuonP4) < matchingDeltaR) continue;
      allMuons->push_back(dsaMuon);
    }
  }

  return allMuons;
}