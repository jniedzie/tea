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
  if (applyScaleFactors["pileup"]) ReadPileupSFs();
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
  for (auto &[name, apply] : applyScaleFactors) {
    info() << "  " << name << ": " << apply << endl;
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
  if (!applyScaleFactors["PUjetID"]) return {{"systematic", 1.0}};

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  scaleFactors["systematic"] = TryToEvaluate(corrections[name], {eta, pt, extraArgs["systematic"], extraArgs["workingPoint"]});  
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {eta, pt, variation, extraArgs["workingPoint"]});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonScaleFactors(string name, float eta, float pt) {
  if (!applyScaleFactors["muon"]) return {{"systematic", 1.0}};

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  scaleFactors["systematic"] = TryToEvaluate(corrections[name], {fabs(eta), pt, extraArgs["systematic"]});
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetDSAMuonScaleFactors(string name, float eta, float pt) {
  if (!applyScaleFactors["muon"]) return {{"systematic", 1.0}};

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  scaleFactors["systematic"] = TryToEvaluate(corrections[name], {extraArgs["year"], fabs(eta), pt, extraArgs["systematic"]});
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {extraArgs["year"], fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonTriggerScaleFactors(string name, float eta, float pt) {
  if (!applyScaleFactors["muonTrigger"]) return {{"systematic", 1.0}};

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  scaleFactors["systematic"] = TryToEvaluate(corrections[name], {fabs(eta), pt, extraArgs["systematic"]});
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetBTagScaleFactors(string name, float eta, float pt) {
  if (!applyScaleFactors["bTagging"]) return {{"systematic", 1.0}};

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  scaleFactors["systematic"] = TryToEvaluate(corrections[name], {extraArgs["systematic"], extraArgs["workingPoint"], stoi(extraArgs["jetID"]), eta, pt});
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {variation, extraArgs["workingPoint"], stoi(extraArgs["jetID"]), eta, pt});
  }
  return scaleFactors;
}

vector<string> ScaleFactorsManager::GetBTagVariationNames(string name) {
  vector<string> variations;
  if (!applyScaleFactors["bTagging"]) return variations;

  auto extraArgs = correctionsExtraArgs[name];
  variations = GetScaleFactorVariations(extraArgs["variations"]);
  return variations;
}


float ScaleFactorsManager::GetPileupScaleFactor(string name, float nVertices) {
  if (!applyScaleFactors["pileup"]) return 1.0;

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
  if (!applyScaleFactors["pileup"]) return 1.0;

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
