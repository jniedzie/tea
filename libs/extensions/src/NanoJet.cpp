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
  return scaleFactorsManager.GetBTagScaleFactors(workingPoint, GetAbsEta(), GetPt());
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

void NanoJet::AddSmearedPtByResolution(float rho, int eventID, shared_ptr<NanoEvent> event) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  float pt = GetPt();

  // ScaleFactor
  map<string,float> jerSF = scaleFactorsManager.GetJetEnergyResolutionScaleFactorAndPtResolution((float)physicsObject->Get("eta"), GetPt(), rho);

  float genPt = -1;
  auto genJet = GetGenJetAsRecommendedForJER(event, jerSF["PtResolution"]);
  if (genJet)
    genPt = genJet->Get("pt");

  map<string, std::variant<int,double,string>> inputs  = {{"JetPt", GetPt()}};
  inputs["JetEta"] = (float)physicsObject->Get("eta");
  inputs["GenPt"] = genPt;
  inputs["Rho"] = rho;
  inputs["EventID"] = eventID;
  inputs["JER"] = jerSF["PtResolution"];
  inputs["JERSF"] = jerSF["systematic"];

  float jetPt_factor = scaleFactorsManager.GetJetEnergyResolutionSmearingFactor(inputs);
  inputs["JERSF"] = jerSF["jerMC_ScaleFactor_up"];
  float jetPt_factor_up = scaleFactorsManager.GetJetEnergyResolutionSmearingFactor(inputs);
  inputs["JERSF"] = jerSF["jerMC_ScaleFactor_down"];
  float jetPt_factor_down = scaleFactorsManager.GetJetEnergyResolutionSmearingFactor(inputs);

  physicsObject->SetFloat("pt_smeared" , GetPt()*jetPt_factor);
  physicsObject->SetFloat("pt_smeared_up" , GetPt()*jetPt_factor_up);
  physicsObject->SetFloat("pt_smeared_down" , GetPt()*jetPt_factor_down);
  physicsObject->SetFloat("mass_smeared" , GetMass()*jetPt_factor);
  physicsObject->SetFloat("mass_smeared_up" , GetMass()*jetPt_factor_up);
  physicsObject->SetFloat("mass_smeared_down" , GetMass()*jetPt_factor_down);
}

shared_ptr<PhysicsObject> NanoJet::GetGenJetAsRecommendedForJER(shared_ptr<NanoEvent> event, float sigma_JER, float R_cone) {
  shared_ptr<PhysicsObjects> genJets = event->GetCollection("GenJet");
  float eta = physicsObject->Get("eta");
  float phi = physicsObject->Get("phi");
  for (auto genJet : *genJets) {
    float dEta = eta - float(genJet->Get("eta"));
    float dPhi = TVector2::Phi_mpi_pi(phi - float(genJet->Get("phi")));
    float dR = TMath::Sqrt(dEta * dEta + dPhi * dPhi);
    if (dR >= R_cone / 2) 
      continue;

    float absDPt = fabs(GetPt() - (float)genJet->Get("pt"));
    if (absDPt >= 3 * sigma_JER * GetPt())
      continue;

    return genJet;
  }
  return nullptr;
}

float NanoJet::GetPxDifference(float newJetPt, float oldJetPt) {
  float phi = GetPhi();
  if (oldJetPt < 0)
    oldJetPt = GetPt();
  float deltaPt = newJetPt - oldJetPt;
  return deltaPt * cos(phi);
}

float NanoJet::GetPyDifference(float newJetPt, float oldJetPt) {
  float phi = GetPhi();
  if (oldJetPt < 0)
    oldJetPt = GetPt();
  float deltaPt = newJetPt - oldJetPt;
  return deltaPt * sin(phi);
}

bool NanoJet::IsInCollection(const shared_ptr<PhysicsObjects> collection) {
  for (auto object : *collection) {
    if (physicsObject == object) {
      return true;
    }
  }
  return false;
}
