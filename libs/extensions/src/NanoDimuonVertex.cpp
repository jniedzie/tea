#include "NanoDimuonVertex.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoDimuonVertex::NanoDimuonVertex(shared_ptr<PhysicsObject> physicsObject_, const shared_ptr<Event> event)
    : physicsObject(physicsObject_) {
  if (IsDSAMuon1() || IsDSAMuon2()) hasDSAMuon = true;
  if (!IsDSAMuon1() || !IsDSAMuon2()) hasPatMuon = true;
  auto muons = GetMuons(event);
  muon1 = muons.first;
  muon2 = muons.second;

  Lxyz.SetXYZ(GetAs<float>("vx") - event->GetAs<float>("PV_x"), GetAs<float>("vy") - event->GetAs<float>("PV_y"),
              GetAs<float>("vz") - event->GetAs<float>("PV_z"));
  float PV_err = sqrt(event->GetAs<float>("PV_chi2"));
  LxySigma = (1 / GetLxyFromPV()) * sqrt(pow(Lxyz.X(), 2) * (pow(GetAs<float>("vxErr"), 2) + pow(PV_err, 2)) +
                                         pow(Lxyz.Y(), 2) * (pow(GetAs<float>("vyErr"), 2) + pow(PV_err, 2)));
}

string NanoDimuonVertex::GetVertexCategory() {
  string originalCollection = physicsObject->GetOriginalCollection();

  if (originalCollection.substr(0, 6) == "PatDSA") return "PatDSA";
  if (originalCollection.substr(0, 3) == "Pat") return "Pat";
  if (originalCollection.substr(0, 3) == "DSA") return "DSA";
  return "";
}

pair<shared_ptr<NanoMuon>, shared_ptr<NanoMuon>> NanoDimuonVertex::GetMuons(const shared_ptr<Event> event) {
  shared_ptr<NanoMuon> muon1_, muon2_;

  if (hasPatMuon) {
    auto muons = asNanoMuons(event->GetCollection("Muon"));
    for (auto muon : *muons) {
      // look for muon 1
      if (!IsDSAMuon1() && MuonIndex1() == float(muon->Get("idx"))) {
        muon1_ = muon;
      }
      // look for muon 2
      if (!IsDSAMuon2() && MuonIndex2() == float(muon->Get("idx"))) {
        muon2_ = muon;
      }
    }
  }
  if (hasDSAMuon) {
    auto muons = asNanoMuons(event->GetCollection("DSAMuon"));
    for (auto muon : *muons) {
      // look for muon 1
      if (IsDSAMuon1() && MuonIndex1() == float(muon->Get("idx"))) {
        muon1_ = muon;
      }
      // look for muon 2
      if (IsDSAMuon2() && MuonIndex2() == float(muon->Get("idx"))) {
        muon2_ = muon;
      }
    }
  }
  return make_pair(muon1_, muon2_);
}

TLorentzVector NanoDimuonVertex::GetFourVector() {
  auto muonVector1 = muon1->GetFourVector();
  auto muonVector2 = muon2->GetFourVector();
  return muonVector1 + muonVector2;
}

float NanoDimuonVertex::GetCollinearityAngle() {
  auto fourVector = GetFourVector();
  TVector3 ptVector(fourVector.Px(), fourVector.Py(), fourVector.Py());
  return ptVector.DeltaPhi(Lxyz);
}

float NanoDimuonVertex::GetDPhiBetweenMuonpTAndLxy(int muonIndex) {
  std::shared_ptr<NanoMuon> muon;
  if (muonIndex == 1)
    muon = muon1;
  else if (muonIndex == 2)
    muon = muon2;
  else {
    warn() << "Invalid muon index " << muonIndex << " in NanoDimuonVertex::GetMuonpTLxyDPhi" << endl;
    return -5;
  }
  auto muonFourVector = muon->GetFourVector();
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
  if (category == "Pat") return abs(float(muon1->GetAs<float>("trkNumPixelHits")) - float(muon2->GetAs<float>("trkNumPixelHits")));
  return 0;
}

float NanoDimuonVertex::Get3DOpeningAngle() {
  auto muon1fourVector = muon1->GetFourVector();
  auto muon2fourVector = muon2->GetFourVector();
  auto muon1Vector = muon1fourVector.Vect();
  auto muon2Vector = muon2fourVector.Vect();
  return muon1Vector.Angle(muon2Vector);
}

float NanoDimuonVertex::GetCosine3DOpeningAngle() {
  auto angle = Get3DOpeningAngle();
  return cos(angle);
}

float NanoDimuonVertex::GetDimuonChargeProduct() { return float(muon1->GetAs<float>("charge")) * float(muon2->GetAs<float>("charge")); }

float NanoDimuonVertex::GetOuterDeltaR() {
  float outerEta1 = muon1->GetAs<float>("outerEta");
  float outerPhi1 = muon1->GetAs<float>("outerPhi");
  float outerEta2 = muon2->GetAs<float>("outerEta");
  float outerPhi2 = muon2->GetAs<float>("outerPhi");

  if (outerEta1 <= -5 || outerEta2 <= -5) return -1;
  return muon1->OuterDeltaRtoMuon(muon2);
}

float NanoDimuonVertex::GetDeltaEta() { return muon1->GetAs<float>("eta") - muon2->GetAs<float>("eta"); }

float NanoDimuonVertex::GetDeltaPhi() { return muon1->GetAs<float>("phi") - muon2->GetAs<float>("phi"); }

float NanoDimuonVertex::GetOuterDeltaEta() { return muon1->GetAs<float>("outerEta") - muon2->GetAs<float>("outerEta"); }

float NanoDimuonVertex::GetOuterDeltaPhi() { return muon1->GetAs<float>("outerPhi") - muon2->GetAs<float>("outerPhi"); }

float NanoDimuonVertex::GetLeadingMuonPt() { return max((float)muon1->Get("pt"), (float)muon2->Get("pt")); }

float NanoDimuonVertex::GetDeltaDisplacedTrackIso03()
{
  double iso03_1 = GetAs<float>("displacedTrackIso03Dimuon1");
  double iso03_2 = GetAs<float>("displacedTrackIso03Dimuon2");
  return abs(iso03_1 - iso03_2);
}
float NanoDimuonVertex::GetDeltaDisplacedTrackIso04()
{
  double iso04_1 = GetAs<float>("displacedTrackIso04Dimuon1");
  double iso04_2 = GetAs<float>("displacedTrackIso04Dimuon2");
  return abs(iso04_1 - iso04_2);
}

int NanoDimuonVertex::GetTotalNumberOfSegments() {
  std::string category = GetVertexCategory();
  if (category == "Pat") return 0;
  if (category == "PatDSA") return muon2->GetAs<int>("nSegments");
  return muon1->GetAs<int>("nSegments") + muon2->GetAs<int>("nSegments");
}

int NanoDimuonVertex::GetTotalNumberOfDTHits() {
  std::string category = GetVertexCategory();
  if (category == "Pat") return 0;
  if (category == "PatDSA") return muon2->GetAs<int>("trkNumDTHits");
  return muon1->GetAs<int>("trkNumDTHits") + muon2->GetAs<int>("trkNumDTHits");
}

int NanoDimuonVertex::GetTotalNumberOfCSCHits() {
  std::string category = GetVertexCategory();
  if (category == "Pat") return 0;
  if (category == "PatDSA") return muon2->GetAs<int>("trkNumCSCHits");
  return muon1->GetAs<int>("trkNumCSCHits") + muon2->GetAs<int>("trkNumCSCHits");
}

shared_ptr<NanoMuon> NanoDimuonVertex::GetLeadingMuon() {
  return (muon1->GetAs<float>("pt") > muon2->GetAs<float>("pt")) ? muon1 : muon2;
}

shared_ptr<NanoMuon> NanoDimuonVertex::GetSubleadingMuon() {
  return (muon1->GetAs<float>("pt") < muon2->GetAs<float>("pt")) ? muon1 : muon2;
}

bool NanoDimuonVertex::HasMuonIndices(int muonIdx1, int muonIdx2) {
  if (Muon1()->GetIdx() == muonIdx1 && Muon2()->GetIdx() == muonIdx2)
    return true;
  return false;
}

string NanoDimuonVertex::GetGenMotherCategory(shared_ptr<PhysicsObjects> genMuonCollection) {
  auto genMothers = GetGenMothers(genMuonCollection);
  if (!genMothers) return "NonResonant";
  if (genMothers->size() != 2) return "NonResonant";

  auto mother1 = genMothers->at(0);
  auto mother2 = genMothers->at(1);
  if (mother1 == mother2) {
    int ALPpdgId = 54;
    if (abs(asNanoGenParticle(mother1)->GetPdgId()) == ALPpdgId) {
      return "FromALP";
    }
    return "Resonant";
  }
  return "NonResonant";
}

shared_ptr<PhysicsObjects> NanoDimuonVertex::GetGenMothers(shared_ptr<PhysicsObjects> genMuonCollection) {

  auto genMothers = make_shared<PhysicsObjects>();

  auto muon1 = Muon1();
  auto muon2 = Muon2();
  auto genMuon1 = muon1->GetGenMuon(genMuonCollection);
  auto genMuon2 = muon2->GetGenMuon(genMuonCollection);
  if (!genMuon1 || !genMuon2) return nullptr;

  auto firstMuon1 = genMuon1->GetFirstCopy(genMuonCollection);
  auto firstMuon2 = genMuon2->GetFirstCopy(genMuonCollection);
  if (!firstMuon1 || !firstMuon2) return nullptr;

  int motherIndex1 = firstMuon1->GetMotherIndex();
  if (motherIndex1 < 0) return nullptr;
  int motherIndex2 = firstMuon2->GetMotherIndex();
  if (motherIndex2 < 0) return nullptr;

  genMothers->push_back(genMuonCollection->at(motherIndex1));
  genMothers->push_back(genMuonCollection->at(motherIndex2));

  return genMothers;
}
