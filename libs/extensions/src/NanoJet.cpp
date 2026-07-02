#include "NanoJet.hpp"
#include "ConfigManager.hpp"
#include "ScaleFactorsManager.hpp"

using namespace std;

NanoJet::NanoJet(shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

TLorentzVector NanoJet::GetFourVector() {
  TLorentzVector v;
  v.SetPtEtaPhiM(GetPtSmeared(), GetEta(), GetPhi(), GetMassSmeared());
  return v;
}

float NanoJet::GetPtSmeared() { 
  if (physicsObject->HasBranch("pt_smeared")) {
    return physicsObject->GetAs<float>("pt_smeared");
  }
  warn() << "Requested pt_smeared branch not found for jet. Returning standard pt." << endl;
  return physicsObject->GetAs<float>("pt"); 
}

float NanoJet::GetPtJES() { 
  if (physicsObject->HasBranch("pt_JES")) {
    return physicsObject->GetAs<float>("pt_JES");
  }
  warn() << "Requested pt_JES branch not found for jet. Returning standard pt." << endl;
  return physicsObject->GetAs<float>("pt"); 
}

float NanoJet::GetMassSmeared() { 
  if (physicsObject->HasBranch("mass_smeared")) {
    return physicsObject->GetAs<float>("mass_smeared");
  }
  warn() << "Requested mass_smeared branch not found for jet. Returning standard mass." << endl;
  return physicsObject->GetAs<float>("mass"); 
}

float NanoJet::GetMassJES() { 
  if (physicsObject->HasBranch("mass_JES")) {
    return physicsObject->GetAs<float>("mass_JES");
  }
  warn() << "Requested mass_JES branch not found for jet. Returning standard mass." << endl;
  return physicsObject->GetAs<float>("mass"); 
}

map<string,float> NanoJet::GetBtaggingScaleFactors(string workingPoint, bool isBJet, string datasetName) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  map<string,float> scale_factors = {{"systematic", 1.0}};  
  if (!scaleFactorsManager.ShouldApplyScaleFactor("bTagging") && !scaleFactorsManager.ShouldApplyVariation("bTagging"))
    return scale_factors;

  int hadronFlavour = abs(GetAs<int>("hadronFlavour"));
  
  // b jet
  string wp_suffix = "";
  string jetEfficiency = "bTaggingEfficiency";
  if (hadronFlavour == 4) { // c jet
    wp_suffix = "_cjet";
    jetEfficiency = "cTaggingEfficiency";
  }
  else if (hadronFlavour != 5) { // light jet
    wp_suffix = "_qjet";
    jetEfficiency = "qTaggingEfficiency";
  }
  string jetWorkingPoint = workingPoint + wp_suffix;
  float taggingEfficiency = scaleFactorsManager.GetJetTagEfficiency(jetEfficiency, datasetName, GetPtSmeared());
  map<string,float> sfs = scaleFactorsManager.GetBTagScaleFactors(jetWorkingPoint, GetAbsEta(), GetPtSmeared());

  for (auto &[name, weight]: sfs) {
    string name_ = name;
    if (wp_suffix != "") {
      size_t pos = name_.find(wp_suffix);
      if (pos != string::npos) 
        name_.erase(pos, wp_suffix.size());
    }
    if (isBJet) {
      scale_factors[name_] = sfs[name];
    } else {
      if (taggingEfficiency == 1 ) // Avoiding unstable efficiencies from low stat datasets. 
        scale_factors[name_] = 1.0;
      else
        scale_factors[name_] = (1 - weight * taggingEfficiency) / (1 - taggingEfficiency);
    }
  }
  
  return scale_factors;
}

map<string,float> NanoJet::GetPUJetIDScaleFactors(string name) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  map<string,float> sfs = scaleFactorsManager.GetPUJetIDScaleFactors(name, GetEta(), GetPtSmeared());
  // PU jet ID only applied to low pT jets with pT < 50 GeV
  if (GetPtSmeared() > 50) {
    for (auto &[name, weight]: sfs) {
      sfs[name] = 1.0;
    }
  }
  return sfs;
}

map<string,float> NanoJet::GetJetEnergyCorrectionUncertainties(float rho) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  float pt = GetPt();
  float rawFactor = Get("rawFactor");

  map<string, float> inputs  = {{"Rho", rho}};
  inputs["JetA"] = (float)physicsObject->Get("area");
  inputs["JetEta"] = (float)physicsObject->Get("eta");
  inputs["JetPt"] = pt * (1 - rawFactor);
  inputs["JetMass"] = (float)physicsObject->Get("mass");
  inputs["JetPhi"] = (float)physicsObject->Get("phi");
  map<string,float> corrections = scaleFactorsManager.GetJetEnergyCorrectionUncertainties(inputs);
  return corrections;
}

map<string,float> NanoJet::GetJetEnergyCorrections(vector<string> jecNames, float rho, uint run) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  float input_pt;
  string originalCollection = GetOriginalCollection();
  if (originalCollection != "CorrT1METJet") {
    float pt = Get("pt");
    float rawFactor = Get("rawFactor");
    input_pt = pt * (1 - rawFactor);
  } else {
    input_pt = Get("rawPt");
  }

  map<string, float> inputs  = {{"Rho", rho}};
  inputs["JetA"] = (float)physicsObject->Get("area");
  inputs["JetEta"] = (float)physicsObject->Get("eta");
  inputs["JetPt"] = input_pt;
  inputs["JetPhi"] = (float)physicsObject->Get("phi");
  inputs["run"] = run;
  map<string,float> corrections = scaleFactorsManager.GetJetEnergyCorrections(jecNames, inputs);
  return corrections;
}

void NanoJet::UpdateJetEnergyScaleVariables(float rho, bool isData, uint run) {
  auto& scaleFactorsManager = ScaleFactorsManager::GetInstance();
  if (!scaleFactorsManager.ShouldApplyScaleFactor("jec")) {
    physicsObject->SetFloat("pt_JES", GetAs<float>("pt"));
    physicsObject->SetFloat("mass_JES", GetAs<float>("mass"));
    return;
  }
  
  string dataStr = isData ? "Data" : "MC";
  vector<string> jecNames = {"jecL1"+dataStr, "jecL2"+dataStr};
  if (isData)
    jecNames.push_back("jecL2L3"+dataStr);
  map<string,float> corrections = GetJetEnergyCorrections(jecNames, rho, run);

  float pt_raw = GetAs<float>("pt") * (1 - GetAs<float>("rawFactor"));
  float raw_mass = GetAs<float>("mass") * (1 - GetAs<float>("rawFactor"));
  float pt1 = pt_raw * corrections["jecL1"+dataStr];
  float mass1 = raw_mass * corrections["jecL1"+dataStr];
  float pt2 = pt1 * corrections["jecL2"+dataStr];
  float mass2 = mass1 * corrections["jecL2"+dataStr];
  float pt3 = pt2;
  float mass3 = mass2;
  if (isData) {
    pt3 = pt2 * corrections["jecL2L3"+dataStr];
    mass3 = mass2 * corrections["jecL2L3"+dataStr];
  }
  physicsObject->SetFloat("pt_JES", pt3);
  physicsObject->SetFloat("mass_JES", mass3);
}

void NanoJet::AddSmearedPtByResolution(float rho, int eventID, shared_ptr<NanoEvent> event) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  float pt = GetPtJES();
  float mass = GetMassJES();

  if (event->IsData()) {
    physicsObject->SetFloat("pt_smeared" , pt);
    physicsObject->SetFloat("pt_smeared_up" , pt);
    physicsObject->SetFloat("pt_smeared_down" , pt);
    physicsObject->SetFloat("mass_smeared" , mass);
    physicsObject->SetFloat("mass_smeared_up" , mass);
    physicsObject->SetFloat("mass_smeared_down" , mass);
    return;
  }

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

  physicsObject->SetFloat("pt_smeared" , pt*jetPt_factor);
  physicsObject->SetFloat("pt_smeared_up" , pt*jetPt_factor_up);
  physicsObject->SetFloat("pt_smeared_down" , pt*jetPt_factor_down);
  physicsObject->SetFloat("mass_smeared" , mass*jetPt_factor);
  physicsObject->SetFloat("mass_smeared_up" , mass*jetPt_factor_up);
  physicsObject->SetFloat("mass_smeared_down" , mass*jetPt_factor_down);
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

    float absDPt = fabs(GetPtJES() - (float)genJet->Get("pt"));
    if (absDPt >= 3 * sigma_JER * GetPtJES())
      continue;

    return genJet;
  }
  return nullptr;
}

float NanoJet::GetPxDifference(float newJetPt, float oldJetPt) {
  float phi = GetPhi();
  float deltaPt = newJetPt - oldJetPt;
  return deltaPt * cos(phi);
}

float NanoJet::GetPyDifference(float newJetPt, float oldJetPt) {
  float phi = GetPhi();
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
