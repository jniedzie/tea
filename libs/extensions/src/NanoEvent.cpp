#include "NanoEvent.hpp"

#include "ExtensionsHelpers.hpp"

using namespace std;

TLorentzVector NanoEvent::GetMetFourVector() {
  TLorentzVector metVector;
  metVector.SetPtEtaPhiM(Get("MET_pt"), 0, Get("MET_phi"), 0);
  return metVector;
}

float NanoEvent::GetMetPt() { return Get("MET_pt"); }

shared_ptr<PhysicsObjects> NanoEvent::GetDRMatchedMuons(float matchingDeltaR)
{
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDsaMuons = GetCollection("LooseDSAMuons");

  auto allMuons = make_shared<PhysicsObjects>();
  for(auto muon : *looseMuons){
    allMuons->push_back(muon);
  }
  for(auto dsaMuon : *looseDsaMuons){
    auto dsaMuonP4 = asNanoMuon(dsaMuon)->GetFourVector();
    bool matchFound = false;
    for(auto muon : *looseMuons){
      auto muonP4 = asNanoMuon(muon)->GetFourVector();
      if(muonP4.DeltaR(dsaMuonP4) < matchingDeltaR) matchFound = true;
    }
    if(matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<PhysicsObjects> NanoEvent::GetOuterDRMatchedMuons(float matchingDeltaR)
{
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDsaMuons = GetCollection("LooseDSAMuons");

  auto allMuons = make_shared<PhysicsObjects>();
  for(auto muon : *looseMuons){
    allMuons->push_back(muon);
  }
  for(auto dsaMuon : *looseDsaMuons){
    bool matchFound = false;
    for(auto muon : *looseMuons){
      if(asNanoMuon(dsaMuon)->OuterDeltaRtoMuon(asNanoMuon(muon)) < matchingDeltaR) matchFound = true;
    }
    if(matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<PhysicsObjects> NanoEvent::GetSegmentMatchedMuons(float minMatchRatio)
{
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDsaMuons = GetCollection("LooseDSAMuons");

  auto allMuons = make_shared<PhysicsObjects>();
  for(auto muon : *looseMuons){
    allMuons->push_back(muon);
  }
  for(auto dsaMuon : *looseDsaMuons){

    float nHits = float(dsaMuon->Get("nSegmentHits"));
    
    bool matchFound = false;
    for(int i=1; i<=5; i++) {
      float ratio_tmp = asNanoMuon(dsaMuon)->GetMatchesForNthBestMatch(i) / nHits;
      if(!matchFound && ratio_tmp >= minMatchRatio) {
        if(MuonIndexExist(looseMuons, asNanoMuon(dsaMuon)->GetMatchIdxForNthBestMatch(i),false)) matchFound = true;
        break;
      }
    }
    if(matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

bool NanoEvent::MuonIndexExist(shared_ptr<PhysicsObjects> objectCollection, float index, bool isDSAMuon) {
  for(auto object : *objectCollection) {
    if(float(object->Get("idx")) == index) {
      if(isDSAMuon && asNanoMuon(object)->isDSAMuon()) return true;
      if(!isDSAMuon && !asNanoMuon(object)->isDSAMuon()) return true;
    }
  }
  return false;
}

float NanoEvent::DeltaR(float eta1, float phi1, float eta2, float phi2) {
  float dEta = eta1 - eta2;
  float dPhi = TVector2::Phi_mpi_pi(phi1-phi2);
  return TMath::Sqrt(dEta*dEta + dPhi*dPhi);
}

shared_ptr<PhysicsObjects> NanoEvent::GetAllMuonVerticesCollection() {

  auto patVertices = GetCollection("PatMuonVertex");
  auto patDsaVertices = GetCollection("PatDSAMuonVertex");
  auto dsaVertices = GetCollection("DSAMuonVertex");

  auto muonVertices = make_shared<PhysicsObjects>();

  for (auto vertex: *patVertices) {
    muonVertices->push_back(vertex);
  }
  for (auto vertex: *patDsaVertices) {
    muonVertices->push_back(vertex);
  }
  for (auto vertex: *dsaVertices) {
    muonVertices->push_back(vertex);
  }
  return muonVertices;
}

shared_ptr<PhysicsObjects> NanoEvent::GetVerticesForMuons(shared_ptr<PhysicsObjects> muonCollection) {

  auto vertices = GetAllMuonVerticesCollection();
  auto muonVertices = make_shared<PhysicsObjects>();

  for(auto vertex : *vertices) {

    bool foundMuon1 = false;
    bool foundMuon2 = false;
    for(auto muon : *muonCollection) {
      // look for muon 1:
      if( float(vertex->Get("isDSAMuon1"))==0 && !asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx1")) ) {
        foundMuon1 = true;
      }
      if( float(vertex->Get("isDSAMuon1"))==1 && asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx1")) ) {
        foundMuon1 = true;
      }
      // look for muon 2
      if( float(vertex->Get("isDSAMuon2"))==0 && !asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx2")) ) {
        foundMuon2 = true;
      }
      if( float(vertex->Get("isDSAMuon2"))==1 && asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx2")) ) {
        foundMuon2 = true;
      }
    }
    if (foundMuon1 && foundMuon2) muonVertices->push_back(vertex);
  }
  return muonVertices;
}

shared_ptr<PhysicsObjects> NanoEvent::GetVertexForDimuon(shared_ptr<PhysicsObject> muon1, shared_ptr<PhysicsObject> muon2) {

  auto muons = make_shared<PhysicsObjects>();
  muons->push_back(muon1);
  muons->push_back(muon2);
  auto dimuonVertex = GetVerticesForMuons(muons);

  return dimuonVertex;
}

float NanoEvent::GetNDSAMuon(string collectionName) {
  auto collection = GetCollection(collectionName);

  float nDSAMuon = 0;
  for(auto object : *collection) {
    if(asNanoMuon(object)->isDSAMuon()) nDSAMuon++;
  }
  return nDSAMuon;
}

float NanoEvent::GetNMuon(string collectionName) {
  auto collection = GetCollection(collectionName);

  float nMuon = 0;
  for(auto object : *collection) {
    if(!asNanoMuon(object)->isDSAMuon()) nMuon++;
  }
  return nMuon;
}

shared_ptr<PhysicsObject> NanoEvent::GetMuonWithIndex(int muon_idx, string collectionName, bool isDSAMuon) {
  auto collection = GetCollection(collectionName);

  for(auto object : *collection) {
    float idx = object->Get("idx");
    bool isDSA = asNanoMuon(object)->isDSAMuon();
    if(idx != muon_idx) continue;
    if(isDSA && isDSAMuon) return object;
    if(!isDSA && !isDSAMuon) return object;
  }
  return nullptr;
}

std::pair<float,int> NanoEvent::GetMinDeltaRToGenMuons(std::shared_ptr<PhysicsObject> recoMuon) {
  
  auto genParticles = event->GetCollection("GenPart");
  float minDR = 999.;
  int minDRIdx = -1;

  for(int idx=0; idx < genParticles->size(); idx++) {
    auto genMuon = genParticles->at(idx);
    auto genMuonFourVector = asNanoGenParticle(genMuon)->GetFourVector(0.105);
    auto recoMuonFourVector = asNanoMuon(recoMuon)->GetFourVector();
    float dR = genMuonFourVector.DeltaR(recoMuonFourVector);
    if(dR < minDR) {
      minDR = dR;
      minDRIdx = idx;
    }
  }
  return std::make_pair(minDR,minDRIdx);
}

std::shared_ptr<PhysicsObjects> NanoEvent::GetDSAMuonsInCollection(std::string muonCollectionName) {
  auto collection = GetCollection(muonCollectionName);
  auto dsaMuons = make_shared<PhysicsObjects>();
  for(auto muon : *collection) {
    if(asNanoMuon(muon)->isDSAMuon()) dsaMuons->push_back(muon);
  }
  return dsaMuons;
}

std::shared_ptr<PhysicsObjects> NanoEvent::GetPatMuonsInCollection(std::string muonCollectionName) {
  auto collection = GetCollection(muonCollectionName);
  auto patMuons = make_shared<PhysicsObjects>();
  for(auto muon : *collection) {
    if(!asNanoMuon(muon)->isDSAMuon()) patMuons->push_back(muon);
  }
  return patMuons;
}
