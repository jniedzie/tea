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

map<string,float> NanoJet::GetJetEnergyCorrectionPtVariations(float rho) {
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

  map<string,float> ptVariations;
  for (auto &[name, correction] : corrections) {
    if (name == "systematic") continue;
    ptVariations[name] = pt*correction;
  }
  return ptVariations;
}

