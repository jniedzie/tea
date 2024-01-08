#include "Jet.hpp"
#include "ConfigManager.hpp"
#include "ScaleFactorsManager.hpp"

using namespace std;

Jet::Jet(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

TLorentzVector Jet::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPt(), GetEta(), GetPhi(), GetMass());
  return v;
}

float Jet::GetBtaggingScaleFactor(string workingPoint) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  float sf = scaleFactorsManager.GetBTagScaleFactor(GetEta(), GetPt(), workingPoint);
  return sf;
}