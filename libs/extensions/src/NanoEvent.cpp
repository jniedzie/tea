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

shared_ptr<PhysicsObjects> NanoEvent::GetSegmentMatchedMuons(int minMatches)
{
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDsaMuons = GetCollection("LooseDSAMuons");

  bool useMatchRatio = false;
  if(minMatches == 0) useMatchRatio=true;

  auto allMuons = make_shared<PhysicsObjects>();
  for(auto muon : *looseMuons){
    allMuons->push_back(muon);
  }
  for(auto dsaMuon : *looseDsaMuons){

    if(useMatchRatio) {
      float nHits = float(dsaMuon->Get("trkNumDTHits")) + float(dsaMuon->Get("trkNumCSCHits"));
      minMatches = static_cast<int>(nHits * 2/3);
    }
    
    bool matchFound = false;
    if(float(dsaMuon->Get("muonMatch1")) >= minMatches) {
      if(IndexExist(looseMuons, dsaMuon->Get("muonMatch1idx")),true) matchFound = true;
    }
    if(!matchFound && float(dsaMuon->Get("muonMatch2")) >= minMatches) {
      if(IndexExist(looseMuons, dsaMuon->Get("muonMatch2idx")),true) matchFound = true;
    }
    if(!matchFound && float(dsaMuon->Get("muonMatch3")) >= minMatches) {
      if(IndexExist(looseMuons, dsaMuon->Get("muonMatch3idx")),true) matchFound = true;
    }
    if(!matchFound && float(dsaMuon->Get("muonMatch4")) >= minMatches) {
      if(IndexExist(looseMuons, dsaMuon->Get("muonMatch4idx")),true) matchFound = true;
    }
    if(!matchFound && float(dsaMuon->Get("muonMatch5")) >= minMatches) {
      if(IndexExist(looseMuons, dsaMuon->Get("muonMatch5idx")),true) matchFound = true;
    }
    if(matchFound == false) allMuons->push_back(dsaMuon);

  }

  return allMuons;
}

bool NanoEvent::IndexExist(shared_ptr<PhysicsObjects> objectCollection, float index, bool isDSAMuon) {
  for(auto object : *objectCollection) {
    if(float(object->Get("idx")) == index) {
      if(isDSAMuon && asNanoMuon(object)->isDSAMuon()) {
        return true;
      }
      if(!isDSAMuon && !asNanoMuon(object)->isDSAMuon()) {
        return true;
      }
    }
  }
  return false;
}

float NanoEvent::DeltaR(float eta1, float phi1, float eta2, float phi2) {
  float dEta = eta1 - eta2;
  float dPhi = TVector2::Phi_mpi_pi(phi1-phi2);
  return TMath::Sqrt(dEta*dEta + dPhi*dPhi);
}

shared_ptr<PhysicsObjects> NanoEvent::GetAllMuonVertexCollections() {

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

  auto vertices = GetAllMuonVertexCollections();
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

pair<shared_ptr<PhysicsObject>,shared_ptr<PhysicsObject>> NanoEvent::GetLooseMuonsInVertex(shared_ptr<PhysicsObject> vertex) {
  bool hasDSAMuon = false;
  bool hasPatMuon = true;
  if(float(vertex->Get("isDSAMuon1"))==1 || float(vertex->Get("isDSAMuon2"))==1) hasDSAMuon = true;
  if(float(vertex->Get("isDSAMuon1"))==1 && float(vertex->Get("isDSAMuon2"))==1) hasPatMuon = false;

  shared_ptr<PhysicsObject> muon1,muon2;

  if(hasPatMuon) {
    auto looseMuons = GetCollection("LooseMuons");
    for(auto muon : * looseMuons) {
      if( float(vertex->Get("isDSAMuon1"))==0 && !asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx1")) ) {
        muon1 = muon;
      }
      if( float(vertex->Get("isDSAMuon1"))==1 && asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx1")) ) {
        muon1 = muon;
      }
      // look for muon 2
      if( float(vertex->Get("isDSAMuon2"))==0 && !asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx2")) ) {
        muon2 = muon;
      }
      if( float(vertex->Get("isDSAMuon2"))==1 && asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx2")) ) {
        muon2 = muon;
      }
    }
  }
  if(hasDSAMuon) {
    auto looseMuons = GetCollection("LooseDSAMuons");
    for(auto muon : * looseMuons) {
      if( float(vertex->Get("isDSAMuon1"))==0 && !asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx1")) ) {
        muon1 = muon;
      }
      if( float(vertex->Get("isDSAMuon1"))==1 && asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx1")) ) {
        muon1 = muon;
      }
      // look for muon 2
      if( float(vertex->Get("isDSAMuon2"))==0 && !asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx2")) ) {
        muon2 = muon;
      }
      if( float(vertex->Get("isDSAMuon2"))==1 && asNanoMuon(muon)->isDSAMuon() && float(muon->Get("idx")) ==  float(vertex->Get("idx2")) ) {
        muon2 = muon;
      }
    }
  }

  return make_pair(muon1,muon2);
}
