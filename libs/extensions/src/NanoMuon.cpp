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

map<string,float> NanoMuon::GetEmptyScaleFactors(string nameID, string nameIso, string nameReco, string year) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  
  map<string,float> emptySF;
  map<string,float> idSF = scaleFactorsManager.GetMuonScaleFactors(nameID, fabs(GetEta()), GetPt());
  map<string,float> isoSF = scaleFactorsManager.GetMuonScaleFactors(nameIso, fabs(GetEta()), GetPt());
  map<string,float> recoSF;
  if (year == "2016preVFP" || year == "2016postVFP" || year == "2017" || year == "2018") {
    recoSF = scaleFactorsManager.GetMuonScaleFactors(nameReco, fabs(GetEta()), GetPt());
    for (auto &[name, weight] : recoSF) {
      emptySF[name] = 1.0;
    }
  }
  for (auto &[name, weight] : idSF) {
    emptySF[name] = 1.0;
  }
  for (auto &[name, weight] : isoSF) {
    emptySF[name] = 1.0;
  }
  return emptySF;
}


map<string,float> NanoMuon::GetScaleFactors(string nameID, string nameIso, string nameReco, string year) {
  if (!scaleFactor.empty()) return scaleFactor;

  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  
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

map<string,float> NanoMuon::GetEmptyDSAScaleFactors(string nameID, string nameReco_cosmic) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  vector<variant<int, double, string>> args_jpsi = {fabs(GetEta()), GetPt()};
  string nameID_jpsi = nameID;
  map<string,float> idSF_jpsi = scaleFactorsManager.GetDSAMuonScaleFactors(nameID_jpsi, args_jpsi);

  vector<variant<int, double, string>> args_reco = {};
  map<string,float> recoSF = scaleFactorsManager.GetDSAMuonScaleFactors(nameReco_cosmic, args_reco);

  map<string,float> emptySF;
  for (auto &[name, weight] : idSF_jpsi) {
    emptySF[name] = 1.0;
  }
  for (auto &[name, weight] : recoSF) {
    emptySF[name] = 1.0;  
  }
  return emptySF;
}

map<string,float> NanoMuon::GetDSAScaleFactors(string nameID, string nameReco_cosmic) {
  if (!scaleFactor.empty()) return scaleFactor;

  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  vector<variant<int, double, string>> args_jpsi = {fabs(GetEta()), GetPt()};
  string nameID_jpsi = nameID;
  map<string,float> idSF_jpsi = scaleFactorsManager.GetDSAMuonScaleFactors(nameID_jpsi, args_jpsi);

  vector<variant<int, double, string>> args_cosmic = {fabs((float)Get("dxyPVTraj"))};
  string nameID_cosmic = nameID + "_cosmic";
  map<string,float> idSF_cosmic = scaleFactorsManager.GetDSAMuonScaleFactors(nameID_cosmic, args_cosmic);

  map<string,float> idSF;
  idSF["systematic"] = idSF_jpsi["systematic"] * idSF_cosmic["systematic"];
  for (auto &[name_jpsi, weight] : idSF_jpsi) {
    if (name_jpsi == "systematic") continue;
    string variation = name_jpsi.substr(nameID_jpsi.size() + 1);
    string name_cosmic = nameID_cosmic + "_" + variation;
    idSF[name_jpsi] = idSF_jpsi[name_jpsi] * idSF_cosmic[name_cosmic];
  }
  vector<variant<int, double, string>> args_reco = {};
  map<string,float> recoSF = scaleFactorsManager.GetDSAMuonScaleFactors(nameReco_cosmic, args_reco);

  scaleFactor["systematic"] = idSF["systematic"] * recoSF["systematic"];
  for (auto &[name, weight] : idSF) {
    if (name == "systematic") continue;
    scaleFactor[name] = idSF[name] * recoSF["systematic"];
  }
  for (auto &[name, weight] : recoSF) {
    if (name == "systematic") continue;
    scaleFactor[name] = idSF["systematic"] * recoSF[name];
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

vector<int> NanoMuon::GetMatchedPATMuonIndices(float minMatchRatio) {
  vector<int> patIndices;
  if (!IsDSA()) return patIndices;

  float nSegments = Get("nSegments");
  for (int i = 1; i <= 5; i++) {
    float ratio_tmp = GetMatchesForNthBestMatch(i) / nSegments;

    if(ratio_tmp >= minMatchRatio) {
      patIndices.push_back(GetMatchIdxForNthBestMatch(i));
    }
  }
  return patIndices;
}

bool NanoMuon::HasPATSegmentMatch(shared_ptr<NanoMuons> patMuonCollection, shared_ptr<Event> event, float minMatchRatio) {
  // Implemented for DSA muons
  if (!IsDSA()) return false;

  float nSegments = Get("nSegments");
  bool matchFound = false;
  for (int i = 1; i <= 5; i++) {
    float ratio_tmp = GetMatchesForNthBestMatch(i) / nSegments;
    if (ratio_tmp >= minMatchRatio) {
      bool matchFound = asNanoEvent(event)->PATMuonIndexExist(patMuonCollection, GetMatchIdxForNthBestMatch(i));
      if (matchFound) return true;
    }
  }
  return false;
}

float NanoMuon::DeltaRtoParticle(shared_ptr<PhysicsObject> particle) {
  float dEta = GetEta() - float(particle->Get("eta"));
  float dPhi = TVector2::Phi_mpi_pi(GetPhi() - float(particle->Get("phi")));
  return TMath::Sqrt(dEta * dEta + dPhi * dPhi);
}

shared_ptr<NanoGenParticle> NanoMuon::GetGenMuon(shared_ptr<PhysicsObjects> genParticles, float maxDeltaR, bool allowNonMuons, shared_ptr<PhysicsObject> excludeGenParticle) {
  shared_ptr<NanoGenParticle> bestGenMuon = nullptr;
  float bestDeltaR = maxDeltaR;

  float eta = GetEta();
  float phi = GetPhi();

  for (auto physObj : *genParticles) {
    auto genParticle = asNanoGenParticle(physObj);
    if (!genParticle->IsMuon() && !allowNonMuons) continue;
    if (!genParticle->IsLastCopy()) continue;
    if (excludeGenParticle && physObj == excludeGenParticle) continue;

    float deltaR = DeltaRtoParticle(physObj);
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

shared_ptr<NanoGenParticle> NanoMuon::GetLastCopyGenMuon(shared_ptr<PhysicsObjects> genParticles, float maxDeltaR, bool allowNonMuons) {
  shared_ptr<NanoGenParticle> bestGenMuon = nullptr;
  float bestDeltaR = maxDeltaR;

  float eta = GetEta();
  float phi = GetPhi();

  for (auto physObj : *genParticles) {
    auto genParticle = asNanoGenParticle(physObj);
    if (!genParticle->IsMuon() && !allowNonMuons) continue;
    if (!genParticle->IsLastCopy()) continue;

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
