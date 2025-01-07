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
  float PV_err = sqrt(event->GetAsFloat("PV_chi2"));
  LxySigma = (1/GetLxyFromPV())*sqrt(pow(Lxyz.X(),2)*(pow(GetAsFloat("vxErr"),2)+pow(PV_err,2))+pow(Lxyz.Y(),2)*(pow(GetAsFloat("vyErr"),2)+pow(PV_err,2)));
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

float NanoDimuonVertex::GetDPhiBetweenMuonpTAndLxy(int muonIndex) {
  std::shared_ptr<PhysicsObject> muon;
  if (muonIndex == 1) muon = muon1;
  else if (muonIndex == 2) muon = muon2;
  else {
    warn() << "Invalid muon index " << muonIndex << " in NanoDimuonVertex::GetMuonpTLxyDPhi" << endl;
    return -5;
  }
  auto muonFourVector = asNanoMuon(muon)->GetFourVector();
  TVector3 ptVector(muonFourVector.Px(), muonFourVector.Py(), muonFourVector.Pz());
  return ptVector.DeltaPhi(Lxyz);
}

float NanoDimuonVertex::GetDPhiBetweenDimuonpTAndPtMiss(TLorentzVector ptMissFourVector) {
  TVector3 ptVector(GetFourVector().Px(), GetFourVector().Py(), GetFourVector().Pz());
  TVector3 ptMissVector(ptMissFourVector.Px(), ptMissFourVector.Py(), ptMissFourVector.Pz());
  return ptVector.DeltaPhi(ptMissVector);
}

float NanoDimuonVertex::GetDeltaPixelHits() {
  std::string category = GetVertexCategory();
  if(category == "Pat") return abs(float(muon1->GetAsFloat("trkNumPixelHits")) - float(muon2->GetAsFloat("trkNumPixelHits")));
  return 0;
}

float NanoDimuonVertex::Get3DOpeningAngle() {
  auto muon1fourVector = asNanoMuon(muon1)->GetFourVector();
  auto muon2fourVector = asNanoMuon(muon2)->GetFourVector();
  auto muon1Vector = muon1fourVector.Vect();
  auto muon2Vector = muon2fourVector.Vect();
  return muon1Vector.Angle(muon2Vector);
}

float NanoDimuonVertex::GetCosine3DOpeningAngle() {
  auto angle = Get3DOpeningAngle();
  return cos(angle);
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

float NanoDimuonVertex::GetDeltaEta() {
  return muon1->GetAsFloat("eta") - muon2->GetAsFloat("eta");
}

float NanoDimuonVertex::GetDeltaPhi() {
  return muon1->GetAsFloat("phi") - muon2->GetAsFloat("phi");
}

float NanoDimuonVertex::GetOuterDeltaEta() {
  return muon1->GetAsFloat("outerEta") - muon2->GetAsFloat("outerEta");
}

float NanoDimuonVertex::GetOuterDeltaPhi() {
  return muon1->GetAsFloat("outerPhi") - muon2->GetAsFloat("outerPhi");
}

float NanoDimuonVertex::GetTotalNumberOfSegments() {
  std::string category = GetVertexCategory();
  if(category=="Pat") return 0;
  if(category=="PatDSA") return muon2->GetAsFloat("nSegments");
  return muon1->GetAsFloat("nSegments") + muon2->GetAsFloat("nSegments");
}

float NanoDimuonVertex::GetTotalNumberOfDTHits() {
  std::string category = GetVertexCategory();
  if(category=="Pat") return 0;
  if(category=="PatDSA") return muon2->GetAsFloat("trkNumDTHits");
  return muon1->GetAsFloat("trkNumDTHits") + muon2->GetAsFloat("trkNumDTHits");
}

float NanoDimuonVertex::GetTotalNumberOfStations() {
  std::string category = GetVertexCategory();
  if(category=="DSA") return 0;
  if(category=="PatDSA") return muon1->GetAsFloat("nStations");
  return muon1->GetAsFloat("nStations") + muon2->GetAsFloat("nStations");
}
