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

map<string,float> NanoJet::GetBtaggingScaleFactors(string workingPoint) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  return scaleFactorsManager.GetBTagScaleFactors(workingPoint, GetEta(), GetPt());
}

map<string,float> NanoJet::GetPUJetIDScaleFactors(string name) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  return scaleFactorsManager.GetPUJetIDScaleFactors(name, GetEta(), GetPt());
}
