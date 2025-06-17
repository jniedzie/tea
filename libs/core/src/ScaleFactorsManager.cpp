//  ScaleFactorsManager.cpp
//
//  Created by Jeremi Niedziela on 01/11/2023.

#include "ScaleFactorsManager.hpp"

#include "ConfigManager.hpp"

using namespace std;

#ifdef USE_CORRECTIONLIB
#include "correction.h"
namespace correction {
  std::shared_ptr<CorrectionSet> from_file(const std::string &fname);
}
using correction::from_file;
using correction::CorrectionSet;
#else
namespace {
std::shared_ptr<std::map<string, CorrectionRef>> from_file(const string &path) {
  return std::make_shared<std::map<string, CorrectionRef>>();
}
}  // namespace
#endif

ScaleFactorsManager::ScaleFactorsManager() {
  ReadScaleFactorFlags();
  ReadScaleFactors();
  if (ShouldApplyScaleFactor("pileup")) ReadPileupSFs();
}

bool ScaleFactorsManager::ShouldApplyScaleFactor(const std::string &name) {
  return applyScaleFactors.count(name) ? applyScaleFactors[name][0] : false;
}

bool ScaleFactorsManager::ShouldApplyVariation(const std::string &name) {
  return applyScaleFactors.count(name) ? applyScaleFactors[name][1] : false;
}

void ScaleFactorsManager::ReadScaleFactors() {
#ifndef USE_CORRECTIONLIB
  return;
#endif

  auto &config = ConfigManager::GetInstance();

  map<string, map<string, string>> scaleFactors;
  config.GetMap("scaleFactors", scaleFactors);

  for (auto &[name, values] : scaleFactors) {
    auto cset = from_file(values["path"]);
    map<string, string> extraArgs;

    for (auto &[key, value] : values) {
      if (key == "path" || key == "type") continue;
      extraArgs[key] = value;
    }
    if (corrections.count(name)) continue;

    if (name.find("jec") != std::string::npos) continue;
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

void ScaleFactorsManager::ReadJetEnergyCorrections() {
  if(!applyScaleFactors["jec"][0] && !applyScaleFactors["jec"][1]) return;
  applyJEC = true;
  auto &config = ConfigManager::GetInstance();
  try {
    config.GetValue("sampleType", sampleType);
  } catch (const Exception &e) {
    info() << "Couldn't read sampleType from config file - will assume MC sample" << endl;
    sampleType = "MC";
  }
  try {
    config.GetValue("sampleEra", sampleEra);
  } catch (const Exception &e) {
    info() << "Couldn't read sampleEra from config file - will assume MC sample" << endl;
    sampleEra = "";
  }

  map<string, map<string, string>> scaleFactors;
  config.GetMap("scaleFactors", scaleFactors);

  for (auto &[name, values] : scaleFactors) {
    if (name.find("jec") == std::string::npos) continue;
    auto cset = correction::CorrectionSet::from_file(values["path"]);

    if (corrections.count(name)) continue;
    if (sampleType != values["sampleType"]) continue;

    string type = GetJetEnergyCorrectionType(name, values, sampleType, sampleEra);
    try {
      compoundCorrections[name] = cset->compound().at(type);
      correctionsExtraArgs[name] = values;
    } catch (std::out_of_range &e) {
      fatal() << "Incorrect correction type: " << type << endl;
      fatal() << "Available corrections: " << endl;
      for (auto &[name, corr] : *cset) fatal() << name << endl;
      exit(0);
    }
    vector<string> uncertainties = GetScaleFactorVariations(values["uncertainties"]);
    for (auto uncertainty : uncertainties) {
      string unc_type = GetJetEnergyCorrectionType(name, values, sampleType, sampleEra, uncertainty);
      string unc_name = name + "_" + uncertainty;
      if (corrections.count(unc_name)) continue;
      try {
        corrections[unc_name] = cset->at(unc_type);
        correctionsExtraArgs[unc_name] = values;
      } catch (std::out_of_range &e) {
        fatal() << "Incorrect correction type: " << unc_type << endl;
        fatal() << "Available corrections: " << endl;
        for (auto &[name, corr] : *cset) fatal() << name << endl;
        exit(0);
      }
    }
    
  }
}

string ScaleFactorsManager::GetJetEnergyCorrectionType(string name, map<string, string> values, string sampleType, string sampleEra, string uncertainty) {
  if (uncertainty == "")
    return values["campaign"] + sampleEra + "_" + values["version"] + "_" + sampleType + "_" + values["level"] + "_" + values["algo"];

  return values["campaign"] + sampleEra + "_" + values["version"] + "_" + sampleType + "_" + uncertainty + "_" + values["algo"];
}

bool ScaleFactorsManager::ReadScaleFactorFlags() {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetMap("applyScaleFactors", applyScaleFactors);
  } catch (Exception &e) {
    warn() << "Couldn't read applyScaleFactors from config." << endl;
  }

    info() << "\n------------------------------------" << endl;
    info() << "Applying scale factors:" << endl;
    for (auto &[name, applyVector] : applyScaleFactors) {
      info() << "  " << name << ": " << applyVector[0] << ", " << applyVector[1] << endl;
    }
    info() << "------------------------------------\n" << endl;
  } catch (const Exception &e) {
    warn() << "Couldn't read applyScaleFactors from config file - no scale factors will be applied" << endl;
    return false;
  }
  return true;
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
  bool applyDefault = ShouldApplyScaleFactor("PUjetID");
  bool applyVariations = ShouldApplyVariation("PUjetID");

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested PUJetID SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(corrections[name], {eta, pt, extraArgs["systematic"], extraArgs["workingPoint"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {eta, pt, variation, extraArgs["workingPoint"]});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("muon");
  bool applyVariations = ShouldApplyVariation("muon");

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested muon SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(corrections[name], {fabs(eta), pt, extraArgs["systematic"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(corrections[name], {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetDSAMuonScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("muon");
  bool applyVariations = ShouldApplyVariation("muon");

  if (corrections.find(dsaname) == corrections.end()) {
    warn() << "Requested DSA muon SF, which was not defined in the scale_factors_config: " << dsaname << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[dsaname];
  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(corrections[name], {extraArgs["year"], fabs(eta), pt, extraArgs["systematic"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[patname + "_" + variation] = TryToEvaluate(corrections[dsaname], {extraArgs["year"], fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonTriggerScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("muonTrigger");
  bool applyVariations = ShouldApplyVariation("muonTrigger");

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested muon trigger SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
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
  bool applyDefault = ShouldApplyScaleFactor("bTagging");
  bool applyVariations = ShouldApplyVariation("bTagging");

  if (corrections.find(name) == corrections.end()) {
    warn() << "Requested bTag SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] =
        TryToEvaluate(corrections[name], {extraArgs["systematic"], extraArgs["workingPoint"], stoi(extraArgs["jetID"]), eta, pt});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] =
        TryToEvaluate(corrections[name], {variation, extraArgs["workingPoint"], stoi(extraArgs["jetID"]), eta, pt});
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

  auto extraArgs = correctionsExtraArgs[name];
  return TryToEvaluate(corrections[name], {nVertices, extraArgs["weights"]});
}

float ScaleFactorsManager::TryToEvaluate(const CorrectionRef &correction, const vector<std::variant<int, double, std::string>> &args) {
#ifndef USE_CORRECTIONLIB
  return 1.0;
#else
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
#endif
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
  else if (category == "")
    scaleFactors["systematic"] = 1.0;
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

map<string, float> ScaleFactorsManager::GetJetEnergyCorrections(std::map<std::string, float> inputArguments) {
  bool applyDefault = applyScaleFactors["jec"][0];
  bool applyVariations = applyScaleFactors["jec"][1];

  string name = "jec" + sampleType;
  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  else {
    vector<correction::Variable::Type> inputs;
    for (const correction::Variable& input: compoundCorrections[name]->inputs()) {
      inputs.push_back(inputArguments.at(input.name()));
    }
    scaleFactors["systematic"] = compoundCorrections[name]->evaluate(inputs);
  }
  if (!applyVariations) return scaleFactors;

  vector<string> uncertainties = GetScaleFactorVariations(extraArgs["uncertainties"]);
  for (auto uncertainty : uncertainties) {
    string unc_name = name + "_" + uncertainty;
    string type = GetJetEnergyCorrectionType(name, extraArgs, sampleType, sampleEra, uncertainty);
    vector<correction::Variable::Type> unc_inputs;
    for (const correction::Variable& input: corrections[unc_name]->inputs()) {
      unc_inputs.push_back(inputArguments.at(input.name()));
    }
    scaleFactors[unc_name] = TryToEvaluate(corrections[unc_name], unc_inputs);
  }


  return scaleFactors;
}
