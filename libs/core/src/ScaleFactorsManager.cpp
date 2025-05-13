//  ScaleFactorsManager.cpp
//
//  Created by Jeremi Niedziela on 01/11/2023.

#include "ScaleFactorsManager.hpp"

#include "ConfigManager.hpp"

using namespace std;
using correction::CorrectionSet;

ScaleFactorsManager::ScaleFactorsManager() {
  ReadScaleFactorFlags();
  ReadScaleFactors();
  if (applyScaleFactors["pileup"][0]) ReadPileupSFs();
}

void ScaleFactorsManager::ReadScaleFactors() {
  auto &config = ConfigManager::GetInstance();

  map<string, map<string, string>> scaleFactors;
  config.GetMap("scaleFactors", scaleFactors);
  
  for (auto &[name, values] : scaleFactors) {
    auto cset = correction::CorrectionSet::from_file(values["path"]);
    map<string, string> extraArgs;

    for (auto &[key, value] : values) {
      if (key == "path" || key == "type") continue;
      extraArgs[key] = value;
    }
    if (corrections.count(name)) continue;

    try {
      corrections[name] = cset->at(values["type"]);
      correctionsExtraArgs[name] = extraArgs;
    } catch (std::out_of_range &e) {
      fatal() << "Incorrect correction type: " << values["type"] << endl;
      fatal() << "Available corrections: " << endl;
      for (auto &[name, corr] : *cset) fatal() << name << endl;
      exit(0);
    }
  }
}

void ScaleFactorsManager::ReadScaleFactorFlags() {
  auto &config = ConfigManager::GetInstance();
  config.GetMap("applyScaleFactors", applyScaleFactors);

  info() << "\n------------------------------------" << endl;
  info() << "Applying scale factors:" << endl;
  for (auto &[name, applyVector] : applyScaleFactors) {
    info() << "  " << name << ": " << applyVector[0] << ", " << applyVector[1] << endl;
  }
  info() << "------------------------------------\n" << endl;
}

void ScaleFactorsManager::ReadPileupSFs() {
  auto &config = ConfigManager::GetInstance();

  string pileupScaleFactorsPath, pileupScaleFactorsHistName;
  config.GetValue("pileupScaleFactorsPath", pileupScaleFactorsPath);
  config.GetValue("pileupScaleFactorsHistName", pileupScaleFactorsHistName);
  info() << "Reading pileup scale factors from file: " << pileupScaleFactorsPath << "\thistogram: " << pileupScaleFactorsHistName << endl;
  pileupSFvalues = (TH1D *)TFile::Open(pileupScaleFactorsPath.c_str())->Get(pileupScaleFactorsHistName.c_str());
}

map<string, float> ScaleFactorsManager::GetPUJetIDScaleFactors(string name, float eta, float pt) {
  bool applyDefault = applyScaleFactors["PUjetID"][0];
  bool applyVariations = applyScaleFactors["PUjetID"][1];

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested PUJetID SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  else scaleFactors["systematic"] = TryToEvaluate(corrections[name], {eta, pt, extraArgs["systematic"], extraArgs["workingPoint"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {eta, pt, variation, extraArgs["workingPoint"]});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonScaleFactors(string name, float eta, float pt) {
  bool applyDefault = applyScaleFactors["muon"][0];
  bool applyVariations = applyScaleFactors["muon"][1];

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested muon SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  else scaleFactors["systematic"] = TryToEvaluate(corrections[name], {fabs(eta), pt, extraArgs["systematic"]});
  if(!applyVariations) return scaleFactors;
  
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetDSAMuonScaleFactors(string name, float eta, float pt) {
  bool applyDefault = applyScaleFactors["muon"][0];
  bool applyVariations = applyScaleFactors["muon"][1];

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested DSA muon SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  else scaleFactors["systematic"] = TryToEvaluate(corrections[name], {extraArgs["year"], fabs(eta), pt, extraArgs["systematic"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {extraArgs["year"], fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonTriggerScaleFactors(string name, float eta, float pt) {
  bool applyDefault = applyScaleFactors["muonTrigger"][0];
  bool applyVariations = applyScaleFactors["muonTrigger"][1];

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested muon trigger SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(corrections[name], {fabs(eta), pt, extraArgs["systematic"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetBTagScaleFactors(string name, float eta, float pt) {
  bool applyDefault = applyScaleFactors["bTagging"][0];
  bool applyVariations = applyScaleFactors["bTagging"][1];

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested bTag SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(corrections[name], {extraArgs["systematic"], extraArgs["workingPoint"], stoi(extraArgs["jetID"]), eta, pt});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {variation, extraArgs["workingPoint"], stoi(extraArgs["jetID"]), eta, pt});
  }
  return scaleFactors;
}

vector<string> ScaleFactorsManager::GetBTagVariationNames(string name) {
  vector<string> variations;
  if (!applyScaleFactors["bTagging"][1]) return variations;

  auto extraArgs = correctionsExtraArgs[name];
  variations = GetScaleFactorVariations(extraArgs["variations"]);
  return variations;
}


float ScaleFactorsManager::GetPileupScaleFactor(string name, float nVertices) {
  if (!applyScaleFactors["pileup"][0]) return 1.0;

  cout << "Getting pileup scale factor (2)" << endl;

  auto extraArgs = correctionsExtraArgs[name];
  return TryToEvaluate(corrections[name], {nVertices, extraArgs["weights"]});
}

float ScaleFactorsManager::TryToEvaluate(const correction::Correction::Ref &correction, const vector<std::variant<int, double, std::string>> &args) {
  try {
    return correction->evaluate(args);
  } catch (std::runtime_error &e) {
    string errorMessage = e.what();
    error() << "Error while evaluating SF" << endl;

    if (errorMessage.find("inputs") != string::npos) {
      fatal() << "Expected inputs: " << endl;
      for (auto corr : correction->inputs()) fatal() << corr.name() << "\t" << corr.description() << endl;
      exit(0);
    } else if (errorMessage.find("bounds") != string::npos) {
      warn() << "Encountered a value out of SF bounds. Will assume SF = 1.0 " << endl;
      return 1.0;
    } else {
      fatal() << "Unhandled error while evaluating SF: " << errorMessage << endl;
      exit(0);
    }
  }
}

float ScaleFactorsManager::GetPileupScaleFactorCustom(int nVertices) {
  if (!applyScaleFactors["pileup"][0]) return 1.0;

  if (nVertices < pileupSFvalues->GetXaxis()->GetBinLowEdge(1)) {
    warn() << "Number of vertices is lower than the lowest bin edge in pileup SF histogram" << endl;
    return 1.0;
  }
  if (nVertices > pileupSFvalues->GetXaxis()->GetBinUpEdge(pileupSFvalues->GetNbinsX())) {
    warn() << "Number of vertices is higher than the highest bin edge in pileup SF histogram" << endl;
    return 1.0;
  }

  float sf = pileupSFvalues->GetBinContent(pileupSFvalues->FindFixBin(nVertices));
  return sf;
}

vector<string> ScaleFactorsManager::GetScaleFactorVariations(string variations_str) {
  vector<string> variations;
  stringstream ss(variations_str);
  string item;

  while (getline(ss, item, ',')) {
    variations.push_back(item);
  }
  return variations;
}

map<string, float> ScaleFactorsManager::GetCustomScaleFactorsForCategory(string name, string category) {
  bool applyDefault = applyScaleFactors[name][0];
  bool applyVariations = applyScaleFactors[name][1];
  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  // handle empty category - needed to setup the scale factor names for the first event
  else if (category == "") scaleFactors["systematic"] = 1.0;
  else 
    scaleFactors["systematic"] = TryToEvaluate(corrections[name], {category, extraArgs["systematic"]});

  if (!applyVariations) return scaleFactors;
  
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    if (category == "") {
      scaleFactors[name + "_" + variation] = 1.0;
      continue;
    }
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {category, variation});
  }
  return scaleFactors;
}
