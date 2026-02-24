#include "NanoDimuonVertex.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoDimuonVertex::NanoDimuonVertex(shared_ptr<PhysicsObject> physicsObject_, const shared_ptr<Event> event)
    : physicsObject(physicsObject_) {
  string originalCollection = physicsObject_->GetOriginalCollection();
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

float NanoDimuonVertex::GetLogDisplacedTrackIso(string isolationVariable)
{
  double iso = GetAs<float>(isolationVariable);
  if (iso == 0)
    return -3.0;
  return TMath::Log10(iso);
}
float NanoDimuonVertex::GetDeltaDisplacedTrackIso03()
{
  double iso03_1 = GetAs<float>("displacedTrackIso03Dimuon1");
  double iso03_2 = GetAs<float>("displacedTrackIso03Dimuon2");
  return abs(iso03_1 - iso03_2);
}
float NanoDimuonVertex::GetLogDeltaDisplacedTrackIso03()
{
  double delta_iso = GetDeltaDisplacedTrackIso03();
  if (delta_iso == 0)
    return -6.0;
  return TMath::Log10(delta_iso);
}
float NanoDimuonVertex::GetDeltaDisplacedTrackIso04()
{
  double iso04_1 = GetAs<float>("displacedTrackIso04Dimuon1");
  double iso04_2 = GetAs<float>("displacedTrackIso04Dimuon2");
  return abs(iso04_1 - iso04_2);
}
float NanoDimuonVertex::GetLogDeltaDisplacedTrackIso04()
{
  double delta_iso = GetDeltaDisplacedTrackIso04();
  if (delta_iso == 0)
    return -6.0;
  return TMath::Log10(delta_iso);
}
float NanoDimuonVertex::GetLogDeltaSquaredDisplacedTrackIso03()
{
  double delta_iso = GetDeltaDisplacedTrackIso03();
  if (delta_iso == 0)
    return -6.0;
  return TMath::Log10(pow(delta_iso, 2));
}
float NanoDimuonVertex::GetLogDeltaSquaredDisplacedTrackIso04()
{
  double delta_iso = GetDeltaDisplacedTrackIso04();
  if (delta_iso == 0)
    return -6.0;
  return TMath::Log10(pow(delta_iso, 2));
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

string NanoDimuonVertex::GetGenMotherResonanceCategory(shared_ptr<PhysicsObjects> genMuonCollection, const shared_ptr<Event> event, float maxDeltaR) {
  auto genMothers = GetGenMothers(genMuonCollection, event, maxDeltaR);
  if (genMothers->size() != 2) return "NonResonant";
  if (!genMothers->at(0) || !genMothers->at(1)) return "NonResonant";

  auto mother1 = genMothers->at(0);
  auto mother2 = genMothers->at(1);
  if (mother1 == mother2) {
    int ALPpdgId = 54;
    if (fabs(asNanoGenParticle(mother1)->GetPdgId()) == ALPpdgId) {
      return "FromALP";
    }
    if (asNanoGenParticle(mother1)->GetPdgId() == asNanoGenParticle(mother2)->GetPdgId()) {
      return "Resonant";
    }
    return "FalseResonant";
  }
  return "NonResonant";
}

string NanoDimuonVertex::GetGenMotherBackgroundCategory(shared_ptr<PhysicsObjects> genMuonCollection, const shared_ptr<Event> event, float maxDeltaR) {
  auto genMothers = GetGenMothers(genMuonCollection, event, maxDeltaR);
  int pileup_pid = 90; // we define pileup as 90
  int noMother_pid = 80; // we define muons without a mother match as 80
  int mother1_pid = pileup_pid, mother2_pid = pileup_pid;
  if (genMothers->at(0)) {
    mother1_pid = asNanoGenParticle(genMothers->at(0))->GetPdgId();
  } else {
    auto genMuon1 = Muon1()->GetLastCopyGenMuon(genMuonCollection, maxDeltaR);
    if (genMuon1)
      mother1_pid = noMother_pid;
  }
  if (genMothers->at(1)) {
    mother2_pid = asNanoGenParticle(genMothers->at(1))->GetPdgId();
  } else {
    auto genMuon2 = Muon2()->GetLastCopyGenMuon(genMuonCollection, maxDeltaR);
    if (genMuon2)
      mother2_pid = noMother_pid;
  }

  map<string, vector<int>> motherCategories = {
    {"X", {90}},
    {"Y", {80}},
    {"ALP", {54}},
    {"D", {-411, 411, -421, 421, -431, 431}},
    {"B", {-541, 541, -521, 521, -511, 511, -531, 531}},
    // quark q: d, u, s, c, b, t
    {"q", {-1,1,-2,2,-3,3,-4,4,-5,5,-6,6}},
    // lepton l: e, mu
    {"l", {-11,11,-13,13}},
    {"tau", {-15, 15}},
    {"g", {-21,21}},
    {"gamma", {-22,22}},
    {"Z", {-23,23}},
    {"W", {24, -24}},
    // light mesons: rho, pi0, omega, K0, phi, upsilon
    {"lightMeson", {113, 221, 223, 331, 333, 553}},
    {"JPsi", {-443, 443}},
  };
  
  string mother1_category;
  string mother2_category;
  for (const auto &[category, pids] : motherCategories) {
    if (find(pids.begin(), pids.end(), mother1_pid) != pids.end()) {
      mother1_category = category;
      break;
    }
  }
  for (const auto &[category, pids] : motherCategories) {
    if (find(pids.begin(), pids.end(), mother2_pid) != pids.end()) {
      mother2_category = category;
      break;
    }
  }
  if (mother1_category.empty()) {
    mother1_category = "other";
  }
  if (mother2_category.empty()) {
    mother2_category = "other";
  }
  if (mother1_category < mother2_category) {
    return mother1_category + mother2_category;
  }
  return mother2_category + mother1_category;
}


shared_ptr<PhysicsObjects> NanoDimuonVertex::GetGenMothers(shared_ptr<PhysicsObjects> genMuonCollection, const shared_ptr<Event> event, float maxDeltaR) {

  auto genMothers = make_shared<PhysicsObjects>();
  auto genMother1 = make_shared<PhysicsObject>();
  auto genMother2 = make_shared<PhysicsObject>();

  auto muon1 = Muon1();
  auto muon2 = Muon2();
  float noMaxDeltaR = 10000.0;
  auto genMuon1 = muon1->GetGenMuon(genMuonCollection, noMaxDeltaR);
  auto genMuon1LastCopy = muon1->GetLastCopyGenMuon(genMuonCollection, noMaxDeltaR);
  std::shared_ptr<NanoGenParticle> genMuon2;
  if (genMuon1 && genMuon1LastCopy) {
    genMuon2 = muon2->GetGenMuon(genMuonCollection, noMaxDeltaR, false, genMuon1LastCopy->GetPhysicsObject());
  }
  if (genMuon1 && genMuon2) {
    if (genMuon1==genMuon2) {
      cout << " NanoDimuonVertex::GetGenMothers: genMuon1 == genMuon2 " << endl;
    }

    float deltaRsum1 = muon1->DeltaRtoParticle(genMuon1->GetPhysicsObject()) + muon2->DeltaRtoParticle(genMuon2->GetPhysicsObject());
    float deltaRsum2 = muon1->DeltaRtoParticle(genMuon2->GetPhysicsObject()) + muon2->DeltaRtoParticle(genMuon1->GetPhysicsObject());
    if (deltaRsum2 < deltaRsum1) {
      auto temp = genMuon1;
      genMuon1 = genMuon2;
      genMuon2 = temp;
    }
    float deltaR1 = muon1->DeltaRtoParticle(genMuon1->GetPhysicsObject());
    float deltaR2 = muon2->DeltaRtoParticle(genMuon2->GetPhysicsObject());
    if (deltaR1 > maxDeltaR) {
      genMuon1 = nullptr;
    }
    else if (deltaR2 > maxDeltaR) {
      genMuon2 = nullptr;
    }
    // Check if genMuon1 == genMuon2 or 2 same sign gen muons
    else if (genMuon1==genMuon2) {
      genMuon1 = nullptr;
      genMother1 = nullptr;
    } 
    else if (genMuon1->GetPdgId() == genMuon2->GetPdgId()) {
      genMuon1 = nullptr;
      genMother1 = nullptr;
    }
  }
    
  if (!genMuon1) genMother1 = nullptr;
  else {
    auto firstMuon1 = genMuon1->GetFirstCopy(genMuonCollection);
    if (!firstMuon1) genMother1 = nullptr;
    else {
      int motherIndex1 = firstMuon1->GetMotherIndex();
      if (motherIndex1 < 0) genMother1 = nullptr;
      else {
        genMother1 = genMuonCollection->at(motherIndex1);
      }
    }
  }
  if (!genMuon2) genMother2 = nullptr;
  else {
    auto firstMuon2 = genMuon2->GetFirstCopy(genMuonCollection);
    if (!firstMuon2) genMother2 = nullptr;
    else {
      int motherIndex2 = firstMuon2->GetMotherIndex();
      if (motherIndex2 < 0) genMother2 = nullptr;
      else {
        genMother2 = genMuonCollection->at(motherIndex2);
      }
    }
  }

  genMothers->push_back(genMother1);
  genMothers->push_back(genMother2);

  return genMothers;
}
