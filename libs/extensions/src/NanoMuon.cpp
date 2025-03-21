#include "NanoMuon.hpp"
#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

NanoMuon::NanoMuon(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

bool NanoMuon::isTight() { 
  if(isDSA()) return false;
  return physicsObject->Get("tightId"); 
}

TLorentzVector NanoMuon::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPt(), GetEta(), GetPhi(), 0.105);
  return v;
}

float NanoMuon::GetScaleFactor(string nameID, string nameIso, string nameReco, string year) {
  if(scaleFactor > 0) return scaleFactor;
  
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  
  float idSF = 1.0;
  float recoSF = 1.0;
  if(isDSA() && year == "2018") { // TODO: find DSA SF for other years
    nameID = "dsamuonID";
    idSF = scaleFactorsManager.GetDSAMuonScaleFactor(nameID, fabs(GetEta()), GetPt());
  }
  else idSF = scaleFactorsManager.GetMuonScaleFactor(nameID, fabs(GetEta()), GetPt());
  float isoSF = scaleFactorsManager.GetMuonScaleFactor(nameIso, fabs(GetEta()), GetPt());
  // No Muon Reco SF for Run 3 
  if (year == "2016preVFP" || year == "2016postVFP" || year == "2017" || year == "2018") {
    recoSF = scaleFactorsManager.GetMuonScaleFactor(nameReco, fabs(GetEta()), GetPt());
  }
  
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

int NanoMuon::GetMatchIdxForNthBestMatch(int N) {
 string idxString;
 if (isDSA()) idxString = "muonMatch" + to_string(N) + "idx";
 if (!isDSA()) idxString = "dsaMatch" + to_string(N) + "idx";
 return GetAs<int>(idxString);
}

int NanoMuon::GetMatchesForNthBestMatch(int N) {
 string matchString;
 if (isDSA()) matchString = "muonMatch" + to_string(N);
 if (!isDSA()) matchString = "dsaMatch" + to_string(N);
 return GetAs<int>(matchString);
}

shared_ptr<NanoGenParticle> NanoMuon::GetGenMuon(shared_ptr<PhysicsObjects> genParticles, float maxDeltaR){
  shared_ptr<NanoGenParticle> bestGenMuon = nullptr;
  float bestDeltaR = maxDeltaR;

  float eta = GetEta();
  float phi = GetPhi();

  for(auto physObj : *genParticles){
    auto genParticle = asNanoGenParticle(physObj);
    if(!genParticle->IsMuon()) continue;

    float genEta = genParticle->Get("eta");
    float genPhi = genParticle->Get("phi");  
    float dEta = eta - genEta;
    float dPhi = TVector2::Phi_mpi_pi(phi - genPhi);
    float deltaR = TMath::Sqrt(dEta*dEta + dPhi*dPhi);
    if(deltaR < bestDeltaR && deltaR < maxDeltaR){
      bestDeltaR = deltaR;
      bestGenMuon = genParticle;
    }
  }
  return bestGenMuon;

}

float NanoMuon::OuterDeltaRtoMuon(shared_ptr<NanoMuon> muon) {
  float muonEta = muon->GetOuterEta();
  float muonPhi = muon->GetOuterPhi();
  float eta = GetOuterEta();
  float phi = GetOuterPhi();
  float dEta = eta - muonEta;
  float dPhi = TVector2::Phi_mpi_pi(phi - muonPhi);
  return TMath::Sqrt(dEta*dEta + dPhi*dPhi);
}
