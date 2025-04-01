#include "NanoJet.hpp"
#include "ConfigManager.hpp"
#include "ScaleFactorsManager.hpp"

using namespace std;

NanoJet::NanoJet(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

TLorentzVector NanoJet::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPt(), GetEta(), GetPhi(), GetMass());
  return v;
}

float NanoJet::GetBtaggingScaleFactor(string workingPoint, string variant) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  float sf = scaleFactorsManager.GetBTagScaleFactor(workingPoint, GetEta(), GetPt(), variant);
  return sf;
}

float NanoJet::GetPUJetIDScaleFactor(string name, string variant) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  float sf = scaleFactorsManager.GetPUJetIDScaleFactor(name, GetEta(), GetPt(), variant);
  return sf;
}
