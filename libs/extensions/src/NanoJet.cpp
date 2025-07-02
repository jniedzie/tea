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

map<string,float> NanoJet::GetJetEnergyCorrections(float rho) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  float pt = GetPt();
  float rawFactor = Get("rawFactor");

  map<string, float> inputs  = {{"Rho", rho}};
  inputs["JetA"] = (float)physicsObject->Get("area");
  inputs["JetEta"] = (float)physicsObject->Get("eta");
  inputs["JetPt"] = pt * (1 - rawFactor);
  inputs["JetMass"] = (float)physicsObject->Get("mass");
  inputs["JetPhi"] = (float)physicsObject->Get("phi");
  map<string,float> corrections = scaleFactorsManager.GetJetEnergyCorrections(inputs);
  return corrections;
}

float NanoJet::GetDeltaPx(float newJetPt) {
  float phi = GetPhi();
  float oldJetPt = GetPt();
  return newJetPt * cos(phi) - oldJetPt * cos(phi);
}

float NanoJet::GetDeltaPy(float newJetPt) {
  float phi = GetPhi();
  float oldJetPt = GetPt();
  return newJetPt * sin(phi) - oldJetPt * sin(phi);
}

bool NanoJet::IsInCollection(const shared_ptr<PhysicsObjects> collection) {
  for (auto object : *collection) {
    if (physicsObject == object) {
      return true;
    }
  }
  return false;
}
