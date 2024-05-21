#include "NanoDimuonVertex.hpp"
#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoDimuonVertex::NanoDimuonVertex(shared_ptr<PhysicsObject> physicsObject_, const shared_ptr<Event> event) : physicsObject(physicsObject_) {
  auto& config = ConfigManager::GetInstance();
  config.GetMap("muonVertexCuts", muonVertexCuts);

  if(isDSAMuon1() || isDSAMuon2()) hasDSAMuon = true;
  if(!isDSAMuon1() || !isDSAMuon2()) hasPatMuon = true;
  pair<shared_ptr<PhysicsObject>,shared_ptr<PhysicsObject>> muons = GetMuons(event);
  muon1 = muons.first;
  muon2 = muons.second;

  Lxyz.SetXYZ(GetAsFloat("vx") - event->GetAsFloat("PV_x"), GetAsFloat("vy") - event->GetAsFloat("PV_y"), GetAsFloat("vz") - event->GetAsFloat("PV_z"));
}

string NanoDimuonVertex::GetVertexCategory() {
  string originalCollection = physicsObject->GetOriginalCollection();

  if (originalCollection.substr(0, 6) == "PatDSA") return "PatDSA";
  if (originalCollection.substr(0, 3) == "Pat") return "Pat";
  if (originalCollection.substr(0, 3) == "DSA") return "DSA";
  return "";
}

pair<shared_ptr<PhysicsObject>,shared_ptr<PhysicsObject>> NanoDimuonVertex::GetMuons(const shared_ptr<Event> event) {
  shared_ptr<PhysicsObject> muon1_,muon2_;

  if(hasPatMuon) {
    auto muons = event->GetCollection("Muon");
    for(auto muon : * muons) {
      // look for muon 1
      if( !isDSAMuon1() && muonIndex1() == float(muon->Get("idx")) ) {
        muon1_ = muon;
      }
      // look for muon 2
      if( !isDSAMuon2() && muonIndex2() == float(muon->Get("idx")) ) {
        muon2_ = muon;
      }
    }
  }
  if(hasDSAMuon) {
    auto muons = event->GetCollection("DSAMuon");
    for(auto muon : * muons) {
      // look for muon 1
      if( isDSAMuon1() && muonIndex1() == float(muon->Get("idx")) ) {
        muon1_ = muon;
      }
      // look for muon 2
      if( isDSAMuon2() && muonIndex2() == float(muon->Get("idx")) ) {
        muon2_ = muon;
      }
    }
  }
  return make_pair(muon1_,muon2_);
}

TLorentzVector NanoDimuonVertex::GetFourVector() {
  TLorentzVector v;
  auto muonVector1 = asNanoMuon(muon1)->GetFourVector();
  auto muonVector2 = asNanoMuon(muon2)->GetFourVector();
  return muonVector1 + muonVector2;
}

float NanoDimuonVertex::GetCollinearityAngle() {
  TVector2 ptVector(GetFourVector().Px(), GetFourVector().Py());
  TVector2 lxyVector(Lxyz.X(), Lxyz.Y());
  return ptVector.DeltaPhi(lxyVector);
}

float NanoDimuonVertex::GetDeltaPixelHits() {
  std::string category = GetVertexCategory();
  if(category == "Pat") return abs(float(muon1->GetAsFloat("trkNumPixelHits")) - float(muon2->GetAsFloat("trkNumPixelHits")));
  return 0;
}

float NanoDimuonVertex::GetDimuonChargeProduct() {
  return float(muon1->GetAsFloat("charge")) * float(muon2->GetAsFloat("charge"));
}

bool NanoDimuonVertex::PassesDCACut() { 
  return (float)Get("dca") < muonVertexCuts["maxDCA"]; 
}
bool NanoDimuonVertex::PassesChi2Cut() { return (float)Get("normChi2") < muonVertexCuts["maxChi2"]; }
bool NanoDimuonVertex::PassesCollinearityAngleCut() { return abs(GetCollinearityAngle()) < muonVertexCuts["maxCollinearityAngle"]; }
bool NanoDimuonVertex::PassesDeltaPixelHitsCut() { return GetDeltaPixelHits() < muonVertexCuts["maxDeltaPixelHits"]; }
bool NanoDimuonVertex::PassesVxySigmaCut() { return (float)Get("vxySigma") < muonVertexCuts["maxVxySigma"];}
bool NanoDimuonVertex::PassesMaxDeltaRCut() { return (float)Get("dR") < muonVertexCuts["maxDeltaR"]; }
bool NanoDimuonVertex::PassesMinDeltaRCut() { return (float)Get("dR") > muonVertexCuts["minDeltaR"]; }
bool NanoDimuonVertex::PassesLxyCut() { return GetLxyFromPV() > muonVertexCuts["minLxy"]; }

bool NanoDimuonVertex::PassesDimuonChargeCut() { 
  float charge1 = muon1->GetAsFloat("charge");
  float charge2 = muon2->GetAsFloat("charge");
  return charge1 * charge2 == muonVertexCuts["muonChargeProduct"]; 
}

bool NanoDimuonVertex::PassesHitsBeforeVertexCut() { 
  std::string category = GetVertexCategory();
  int hitsInFrontOfVertex = 0;
  if((float)Get("hitsInFrontOfVert1") > 0) hitsInFrontOfVertex += (float)Get("hitsInFrontOfVert1");
  if((float)Get("hitsInFrontOfVert2") > 0) hitsInFrontOfVertex += (float)Get("hitsInFrontOfVert2");
  if(category == "PatDSA") return hitsInFrontOfVertex < muonVertexCuts["maxHitsInFrontOfVertexPatDSA"];
  if(category == "Pat") return hitsInFrontOfVertex < muonVertexCuts["maxHitsInFrontOfVertexPat"];
  if(category == "DSA") return hitsInFrontOfVertex < muonVertexCuts["maxHitsInFrontOfVertexDSA"];
  return false;
}
