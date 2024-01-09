#include "Muon.hpp"
#include "ConfigManager.hpp"

using namespace std;

Muon::Muon(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

TLorentzVector Muon::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPt(), GetEta(), GetPhi(), 0.105);
  return v;
}

float Muon::GetScaleFactor(string nameID, string nameIso, string nameReco) {
  if(scaleFactor > 0) return scaleFactor;
  
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  
  float idSF = scaleFactorsManager.GetMuonScaleFactor(nameID, fabs(GetEta()), GetPt());
  float isoSF = scaleFactorsManager.GetMuonScaleFactor(nameIso, fabs(GetEta()), GetPt());
  float recoSF = scaleFactorsManager.GetMuonScaleFactor(nameReco, fabs(GetEta()), GetPt());
  
  scaleFactor = recoSF * idSF * isoSF;
  return scaleFactor;
}

MuonID Muon::GetID() {
  UChar_t highPtID = Get("highPtId");
  return MuonID(Get("softId"), highPtID == 2, highPtID == 1, Get("tightId"), Get("mediumPromptId"), Get("mediumId"), Get("looseId"));
}

MuonIso Muon::GetIso() {
  UChar_t pfIso = Get("pfIsoId");
  UChar_t tkIso = Get("tkIsoId");
  return MuonIso(tkIso == 1, tkIso == 2, pfIso == 1, pfIso == 2, pfIso == 3, pfIso == 4, pfIso == 5, pfIso == 6);
}