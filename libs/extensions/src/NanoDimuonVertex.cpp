#include "NanoDimuonVertex.hpp"
#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoDimuonVertex::NanoDimuonVertex(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {
  auto& config = ConfigManager::GetInstance();
  config.GetMap("muonVertexCuts", muonVertexCuts);

  if(isDSAMuon1() || isDSAMuon2()) hasDSAMuon = true;
  if(!isDSAMuon1() || !isDSAMuon2()) hasPatMuon = true;
}

string NanoDimuonVertex::GetVertexCategory() {
  string originalCollection = physicsObject->GetOriginalCollection();

  if (originalCollection.substr(0, 6) == "PatDSA") return "PatDSA";
  if (originalCollection.substr(0, 3) == "Pat") return "Pat";
  if (originalCollection.substr(0, 3) == "DSA") return "DSA";
  return "";
}

pair<shared_ptr<PhysicsObject>,shared_ptr<PhysicsObject>> NanoDimuonVertex::GetMuons(const shared_ptr<Event> event) {
  shared_ptr<PhysicsObject> muon1,muon2;

  if(hasPatMuon) {
    auto muons = event->GetCollection("Muon");
    for(auto muon : * muons) {
      if( !isDSAMuon1() && muonIndex1() == float(muon->Get("idx")) ) {
        muon1 = muon;
      }
      // look for muon 2
      if( !isDSAMuon2() && muonIndex2() == float(muon->Get("idx")) ) {
        muon2 = muon;
      }
    }
  }
  if(hasDSAMuon) {
    auto muons = event->GetCollection("DSAMuon");
    for(auto muon : * muons) {
      if( isDSAMuon1() && muonIndex1() == float(muon->Get("idx")) ) {
        muon1 = muon;
      }
      // look for muon 2
      if( isDSAMuon2() && muonIndex2() == float(muon->Get("idx")) ) {
        muon2 = muon;
      }
    }
  }

  return make_pair(muon1,muon2);
}

float NanoDimuonVertex::GetDimuonChargeProduct(const shared_ptr<Event> event) {
  auto muons = GetMuons(event);
  return float(muons.first->GetAsFloat("charge")) * float(muons.second->GetAsFloat("charge"));
}

bool NanoDimuonVertex::PassesChi2Cut() { return (float)Get("chi2") < muonVertexCuts["maxChi2"]; }

bool NanoDimuonVertex::PassesMaxDeltaRCut() { return (float)Get("dR") < muonVertexCuts["maxDeltaR"]; }
bool NanoDimuonVertex::PassesMinDeltaRCut(const shared_ptr<Event> event) { 
  auto muons = GetMuons(event);
  float dR = asNanoMuon(muons.first)->GetFourVector().DeltaR(asNanoMuon(muons.second)->GetFourVector());
  return dR > muonVertexCuts["minDeltaR"];
}

bool NanoDimuonVertex::PassesDimuonChargeCut(const shared_ptr<Event> event) { 
  auto muons = GetMuons(event);
  float charge1 = muons.first->GetAsFloat("charge");
  float charge2 = muons.second->GetAsFloat("charge");
  return charge1 * charge2 == muonVertexCuts["muonChargeProduct"]; 
}
