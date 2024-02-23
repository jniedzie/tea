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

float NanoJet::GetBtaggingScaleFactor(string name) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  float sf = scaleFactorsManager.GetBTagScaleFactor(name, GetEta(), GetPt());
  return sf;
}