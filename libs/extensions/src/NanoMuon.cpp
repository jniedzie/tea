#include "NanoMuon.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoMuon::NanoMuon(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

bool NanoMuon::IsTight() {
  if (IsDSA()) return false;
  return physicsObject->Get("tightId");
}

TLorentzVector NanoMuon::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPt(), GetEta(), GetPhi(), 0.105);
  return v;
}

map<string,float> NanoMuon::GetScaleFactors(string nameID, string nameIso, string nameReco, string year) {
  if (!scaleFactor.empty()) return scaleFactor;

  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  // map<string,float> idSF;
  // if (IsDSA() && year == "2018") {  // TODO: find DSA SF for other years
  //   string dsanameID = "dsamuonID";
  //   idSF = scaleFactorsManager.GetDSAMuonScaleFactors(nameID, dsanameID, fabs(GetEta()), GetPt());
  // } else {
  //   idSF = scaleFactorsManager.GetMuonScaleFactors(nameID, fabs(GetEta()), GetPt());
  // }
  map<string,float> idSF = scaleFactorsManager.GetMuonScaleFactors(nameID, fabs(GetEta()), GetPt());
  map<string,float> isoSF = scaleFactorsManager.GetMuonScaleFactors(nameIso, fabs(GetEta()), GetPt());
  // No Muon Reco SF for Run 3
  map<string,float> recoSF;
  if (year == "2016preVFP" || year == "2016postVFP" || year == "2017" || year == "2018") {
    recoSF = scaleFactorsManager.GetMuonScaleFactors(nameReco, fabs(GetEta()), GetPt());
  }
  else recoSF = {{"systematic", 1.0}};

  scaleFactor["systematic"] = recoSF["systematic"] * idSF["systematic"] * isoSF["systematic"];
  for (auto &[name, weight] : recoSF) {
    if (name == "systematic") continue;
    scaleFactor[name] = recoSF[name] * idSF["systematic"] * isoSF["systematic"];
  }
  for (auto &[name, weight] : idSF) {
    if (name == "systematic") continue;
    scaleFactor[name] = recoSF["systematic"] * idSF[name] * isoSF["systematic"];
  }
  for (auto &[name, weight] : isoSF) {
    if (name == "systematic") continue;
    scaleFactor[name] = recoSF["systematic"] * idSF["systematic"] * isoSF[name];
  }

  return scaleFactor;
}

MuonID NanoMuon::GetID() {
  UChar_t highPtID = Get("highPtId");
  return MuonID(Get("softId"), highPtID == 2, highPtID == 1, Get("tightId"), Get("mediumPromptId"), Get("mediumId"), Get("looseId"));
}

MuonIso NanoMuon::GetIso() {
  UChar_t pfIso = Get("pfIsoId");
  UChar_t tkIso = Get("tkIsoId");
  return MuonIso(tkIso == 1, tkIso == 2, pfIso == 1, pfIso == 2, pfIso == 3, pfIso == 4, pfIso == 5, pfIso == 6);
}

int NanoMuon::GetMatchIdxForNthBestMatch(int N) {
  string idxString;
  if (IsDSA()) idxString = "muonMatch" + to_string(N) + "idx";
  if (!IsDSA()) idxString = "dsaMatch" + to_string(N) + "idx";
  return GetAs<int>(idxString);
}

int NanoMuon::GetMatchesForNthBestMatch(int N) {
  string matchString;
  if (IsDSA()) matchString = "muonMatch" + to_string(N);
  if (!IsDSA()) matchString = "dsaMatch" + to_string(N);
  return GetAs<int>(matchString);
}

shared_ptr<NanoGenParticle> NanoMuon::GetGenMuon(shared_ptr<PhysicsObjects> genParticles, float maxDeltaR, bool allowNonMuons) {
  shared_ptr<NanoGenParticle> bestGenMuon = nullptr;
  float bestDeltaR = maxDeltaR;

  float eta = GetEta();
  float phi = GetPhi();

  for (auto physObj : *genParticles) {
    auto genParticle = asNanoGenParticle(physObj);
    if (!genParticle->IsMuon() && !allowNonMuons) continue;

    float genEta = genParticle->Get("eta");
    float genPhi = genParticle->Get("phi");
    float dEta = eta - genEta;
    float dPhi = TVector2::Phi_mpi_pi(phi - genPhi);
    float deltaR = TMath::Sqrt(dEta * dEta + dPhi * dPhi);
    if (deltaR < bestDeltaR && deltaR < maxDeltaR) {
      bestDeltaR = deltaR;
      bestGenMuon = genParticle;
    }
  }

  if (!bestGenMuon) return nullptr;
  
  auto firstCopy = bestGenMuon->GetFirstCopy(genParticles);
  if (firstCopy) bestGenMuon = firstCopy;

  return bestGenMuon;
}

float NanoMuon::OuterDeltaRtoMuon(shared_ptr<NanoMuon> muon) {
  float muonEta = muon->GetOuterEta();
  float muonPhi = muon->GetOuterPhi();
  float eta = GetOuterEta();
  float phi = GetOuterPhi();
  float dEta = eta - muonEta;
  float dPhi = TVector2::Phi_mpi_pi(phi - muonPhi);
  return TMath::Sqrt(dEta * dEta + dPhi * dPhi);
}

void NanoMuon::Print() {
  const string cyan = "\033[36m";
  const string magenta = "\033[35m";
  const string yellow = "\033[33m";
  const string reset = "\033[0m";

  info() << fixed << setprecision(3);

  info() << cyan << "=== NanoMuon ===" << reset << "\n";
  info() << yellow << left << setw(14) << "pt:" << reset << GetPt() << "\n"
         << yellow << left << setw(14) << "eta:" << reset << GetEta() << "\n"
         << yellow << left << setw(14) << "phi:" << reset << GetPhi() << "\n"
         << yellow << left << setw(14) << "DSA: " << reset << (IsDSA() ? "yes" : "no") << "\n";

  if (!IsDSA()) {
    info() << yellow << left << setw(14) << "ID and Iso:" << reset << "\n";
    GetID().Print();
    GetIso().Print();
  }

  info() << reset;
}
