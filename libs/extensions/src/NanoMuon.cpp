#include "NanoMuon.hpp"
#include "ConfigManager.hpp"

using namespace std;

NanoMuon::NanoMuon(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

TLorentzVector NanoMuon::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPt(), GetEta(), GetPhi(), 0.105);
  return v;
}

float NanoMuon::GetScaleFactor(string nameID, string nameIso, string nameReco) {
  if(scaleFactor > 0) return scaleFactor;
  
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  
  if(isDSAMuon()) nameID = "dsamuonID";
  float idSF = scaleFactorsManager.GetMuonScaleFactor(nameID, fabs(GetEta()), GetPt());
  float isoSF = scaleFactorsManager.GetMuonScaleFactor(nameIso, fabs(GetEta()), GetPt());
  float recoSF = scaleFactorsManager.GetMuonScaleFactor(nameReco, fabs(GetEta()), GetPt());
  
  scaleFactor = recoSF * idSF * isoSF;

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

float NanoMuon::GetMatchIdxForNBestMatch(int N) {
 string idxString;
 if (isDSAMuon()) idxString = "muonMatch" + to_string(N) + "idx";
 if (!isDSAMuon()) idxString = "dsaMatch" + to_string(N) + "idx";
 return GetAsFloat(idxString);
}

float NanoMuon::GetMatchesForNBestMatch(int N) {
 string matchString;
 if (isDSAMuon()) matchString = "muonMatch" + to_string(N);
 if (!isDSAMuon()) matchString = "dsaMatch" + to_string(N);
 return GetAsFloat(matchString);
}

float NanoMuon::OuterDeltaRtoMuon(NanoMuon muon) {
  float muonEta = muon.GetOuterEta();
  float muonPhi = muon.GetOuterPhi();
  float eta = GetOuterPhi();
  float phi = GetOuterPhi();
  float dEta = eta - muonEta;
  float dPhi = TVector2::Phi_mpi_pi(phi - muonPhi);
  return TMath::Sqrt(dEta*dEta + dPhi*dPhi);
}