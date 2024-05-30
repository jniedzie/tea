#include "NanoDimuonVertex.hpp"
#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoDimuonVertex::NanoDimuonVertex(shared_ptr<PhysicsObject> physicsObject_, const shared_ptr<Event> event) : physicsObject(physicsObject_) {
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
  auto fourVector = GetFourVector();
  TVector3 ptVector(fourVector.Px(), fourVector.Py(), fourVector.Py());
  return ptVector.DeltaPhi(Lxyz);
}

float NanoDimuonVertex::GetPATpTLxyDPhi() {
  std::string category = GetVertexCategory();
  if(category == "PatDSA" && !isDSAMuon1() && isDSAMuon2()) {
    auto muonFourVector = asNanoMuon(muon1)->GetFourVector();
    TVector3 ptVector(muonFourVector.Px(), muonFourVector.Py(), muonFourVector.Pz());
    return ptVector.DeltaPhi(Lxyz);
  }
  return -5;
}

float NanoDimuonVertex::GetDeltaPixelHits() {
  std::string category = GetVertexCategory();
  if(category == "Pat") return abs(float(muon1->GetAsFloat("trkNumPixelHits")) - float(muon2->GetAsFloat("trkNumPixelHits")));
  return 0;
}

float NanoDimuonVertex::GetDimuonChargeProduct() {
  return float(muon1->GetAsFloat("charge")) * float(muon2->GetAsFloat("charge"));
}

float NanoDimuonVertex::GetOuterDeltaR() {
  float outerEta1 = muon1->GetAsFloat("outerEta");
  float outerPhi1 = muon1->GetAsFloat("outerPhi");
  float outerEta2 = muon2->GetAsFloat("outerEta");
  float outerPhi2 = muon2->GetAsFloat("outerPhi");

  if (outerEta1 <= -5 || outerEta2 <= -5) return -1;
  return asNanoMuon(muon1)->OuterDeltaRtoMuon(asNanoMuon(muon2));
}
