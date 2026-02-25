//  ScaleFactorsManager.cpp
//
//  Created by Jeremi Niedziela on 01/11/2023.

#include "ScaleFactorsManager.hpp"
#include "ConfigManager.hpp"

#include <zlib.h>
#include <fstream>

using namespace std;
using json = nlohmann::json;

#ifdef USE_CORRECTIONLIB
#include "correction.h"
#else
namespace {
std::shared_ptr<std::map<string, CorrectionRef>> from_file(const string& path) {
  return std::make_shared<std::map<string, CorrectionRef>>();
}
}  // namespace
#endif

ScaleFactorsManager::ScaleFactorsManager() {
#ifdef USE_CORRECTIONLIB
  info() << "Using correctionlib for scale factors." << endl;
#else
  info() << "correctionlib not found, will assume all SFs = 1.0." << endl;
#endif

  ReadScaleFactorFlags();
  ReadScaleFactors();
  if (ShouldApplyScaleFactor("pileup")) ReadPileupSFs();
  ReadJetEnergyCorrections();
}

bool ScaleFactorsManager::ShouldApplyScaleFactor(const std::string& name) {
  return applyScaleFactors.count(name) ? applyScaleFactors[name][0] : false;
}

bool ScaleFactorsManager::ShouldApplyVariation(const std::string& name) {
  return applyScaleFactors.count(name) ? applyScaleFactors[name][1] : false;
}

void ScaleFactorsManager::ExtractBounds(const json& node, map<string, pair<double, double>>& bounds) {
  if (!node.contains("nodetype")) return;

  string type = node["nodetype"];

  if (type == "binning") {
    string input = node["input"];

    const auto& edges = node["edges"];

    auto parseEdge = [](const json& edge) -> double {
      if (edge.is_number()) {
        return edge.get<double>();
      }
      if (edge.is_string()) {
        std::string s = edge.get<std::string>();
        if (s == "Infinity" || s == "inf") return 1e30;
        if (s == "-Infinity" || s == "-inf") return -1e30;
        throw std::runtime_error("Unexpected string edge: " + s);
      }
      throw std::runtime_error("Unsupported edge type in JSON");
    };

    double min = parseEdge(edges.front());
    double max = parseEdge(edges.back());

    bounds[input] = {min, max};

    // recurse into content
    for (const auto& subnode : node["content"]) ExtractBounds(subnode, bounds);
  } else if (type == "category") {
    for (const auto& item : node["content"]) ExtractBounds(item["value"], bounds);
  } else if (type == "multibinning") {
    const auto& inputs = node["inputs"];
    const auto& edges = node["edges"];

    for (size_t i = 0; i < inputs.size(); ++i) {
      std::string input = inputs[i];
      const auto& dimEdges = edges[i];

      double min = dimEdges.front();
      double max = dimEdges.back();

      if (!bounds.count(input)) {
        bounds[input] = {min, max};
      } else {
        bounds[input].first = std::max(bounds[input].first, min);
        bounds[input].second = std::min(bounds[input].second, max);
      }
    }

    // recurse into content
    for (const auto& subnode : node["content"]) ExtractBounds(subnode, bounds);
  } else if (type == "transform") {
    // recurse into content only
    ExtractBounds(node["content"], bounds);
    return;
  }
}

void ScaleFactorsManager::ReadScaleFactors() {
#ifndef USE_CORRECTIONLIB
  return;
#endif
  auto& config = ConfigManager::GetInstance();

  map<string, map<string, string>> scaleFactors;
  config.GetMap("scaleFactors", scaleFactors);

  for (auto& [name, values] : scaleFactors) {
    if (!values.count("path") || !values.count("type")) continue;

    auto cset = correction::CorrectionSet::from_file(values["path"]);
    map<string, string> extraArgs;

    for (auto& [key, value] : values) {
      if (key == "path" || key == "type") continue;
      extraArgs[key] = value;
    }
    if (corrections.count(name)) continue;

    if (name.find("jec") != string::npos) continue;
    try {
      corrections[name] = cset->at(values["type"]);
      correctionsExtraArgs[name] = extraArgs;
    } catch (out_of_range& e) {
      fatal() << "Incorrect correction type: " << values["type"] << endl;
      fatal() << "Available corrections: " << endl;
      for (auto& [name, corr] : *cset) fatal() << name << endl;
      exit(1);
    }

    gzFile file = gzopen(values["path"].c_str(), "rb");
    if (!file) throw std::runtime_error("Cannot open gz file");

    std::string buffer;
    char tmp[4096];
    int bytes;
    while ((bytes = gzread(file, tmp, sizeof(tmp))) > 0) {
      buffer.append(tmp, bytes);
    }
    gzclose(file);

    // Replace non-standard JSON literals
    size_t pos = 0;
    while ((pos = buffer.find("Infinity", pos)) != std::string::npos) {
      buffer.replace(pos, 8, "1e30");
      pos += 4;
    }

    pos = 0;
    while ((pos = buffer.find("-Infinity", pos)) != std::string::npos) {
      buffer.replace(pos, 9, "-1e30");
      pos += 5;
    }

    json fullJson = json::parse(buffer);

    json corrJson;

    for (const auto& c : fullJson["corrections"]) {
      if (c["name"] == values["type"]) {
        corrJson = c;
        break;
      }
    }

    if (corrJson.is_null()) {
      throw std::runtime_error("Correction not found in JSON");
    }

    map<string, pair<double, double>> bounds;
    ExtractBounds(corrJson["data"], bounds);
    boundsPerInput[name] = bounds;
  }
}

void ScaleFactorsManager::ReadJetEnergyCorrections() {
#ifndef USE_CORRECTIONLIB
  return;
#endif

  if (!ShouldApplyScaleFactor("jec") && !ShouldApplyVariation("jec")) return;

  auto& config = ConfigManager::GetInstance();

  map<string, map<string, string>> scaleFactors;
  config.GetMap("scaleFactors", scaleFactors);

  for (auto& [name, values] : scaleFactors) {
    if (name.find("jec") == std::string::npos) continue;
    auto cset = correction::CorrectionSet::from_file(values["path"]);

    if (corrections.count(name)) continue;

    string type = values["type"] + "_" + values["level"] + "_" + values["algo"];
    try {
      compoundCorrections[name] = cset->compound().at(type);
      correctionsExtraArgs[name] = values;
    } catch (std::out_of_range& e) {
      fatal() << "Incorrect correction type: " << type << endl;
      fatal() << "Available corrections: " << endl;
      for (auto& [name, corr] : *cset) fatal() << name << endl;
      exit(1);
    }
    vector<string> uncertainties = GetScaleFactorVariations(values["uncertainties"]);
    for (auto uncertainty : uncertainties) {
      string unc_type = values["type"] + "_" + uncertainty + "_" + values["algo"];
      string unc_name = name + "_" + uncertainty;
      if (corrections.count(unc_name)) continue;
      try {
        corrections[unc_name] = cset->at(unc_type);
        correctionsExtraArgs[unc_name] = values;
      } catch (std::out_of_range& e) {
        fatal() << "Incorrect correction type: " << unc_type << endl;
        fatal() << "Available corrections: " << endl;
        for (auto& [name, corr] : *cset) fatal() << name << endl;
        exit(1);
      }
    }
  }
}

void ScaleFactorsManager::ReadScaleFactorFlags() {
  auto& config = ConfigManager::GetInstance();

  try {
    config.GetMap("applyScaleFactors", applyScaleFactors);
  } catch (Exception& e) {
    warn() << "Couldn't read applyScaleFactors from config." << endl;
  }

  info() << "\n------------------------------------" << endl;
  info() << "Applying scale factors:" << endl;
  for (auto& [name, applyVector] : applyScaleFactors) {
    info() << "  " << name << ": " << applyVector[0] << ", " << applyVector[1] << endl;
  }
  info() << "------------------------------------\n" << endl;
}

void ScaleFactorsManager::ReadPileupSFs() {
  auto& config = ConfigManager::GetInstance();

  string pileupScaleFactorsPath, pileupScaleFactorsHistName;
  config.GetValue("pileupScaleFactorsPath", pileupScaleFactorsPath);
  config.GetValue("pileupScaleFactorsHistName", pileupScaleFactorsHistName);
  info() << "Reading pileup scale factors from file: " << pileupScaleFactorsPath << "\thistogram: " << pileupScaleFactorsHistName << endl;
  pileupSFvalues = (TH1D*)TFile::Open(pileupScaleFactorsPath.c_str())->Get(pileupScaleFactorsHistName.c_str());
}

map<string, float> ScaleFactorsManager::GetPUJetIDScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("PUjetID");
  bool applyVariations = ShouldApplyVariation("PUjetID");

  if (corrections.find(name) == corrections.end()) {
    if (applyDefault || applyVariations)
      warn() << "Requested PUJetID SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }
  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(name, {eta, pt, extraArgs["systematic"], extraArgs["workingPoint"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, {eta, pt, variation, extraArgs["workingPoint"]});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("muon");
  bool applyVariations = ShouldApplyVariation("muon");

  if (corrections.find(name) == corrections.end()) {
    if (applyDefault || applyVariations) warn() << "Requested muon SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(name, {fabs(eta), pt, extraArgs["systematic"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetDSAMuonScaleFactors(string name, const vector<variant<int, double, string>>& args) {
  bool applyDefault = ShouldApplyScaleFactor("dsamuon");
  bool applyVariations = ShouldApplyVariation("dsamuon");

  if (corrections.find(name) == corrections.end()) {
    if (applyDefault || applyVariations)
      warn() << "Requested DSA muon SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }
  auto extraArgs = correctionsExtraArgs[name];
  auto systematic_args = args;
  systematic_args.push_back(extraArgs["systematic"]);
  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(name, systematic_args);
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    auto variation_args = args;
    variation_args.push_back(variation);
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, variation_args);
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetMuonTriggerScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("muonTrigger");
  bool applyVariations = ShouldApplyVariation("muonTrigger");

  if (corrections.find(name) == corrections.end()) {
    if (applyDefault || applyVariations)
      warn() << "Requested muon trigger SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;

  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(name, {fabs(eta), pt, extraArgs["systematic"]});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, {fabs(eta), pt, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetBTagScaleFactors(string name, float eta, float pt) {
  bool applyDefault = ShouldApplyScaleFactor("bTagging");
  bool applyVariations = ShouldApplyVariation("bTagging");

  if (corrections.find(name) == corrections.end()) {
    if (applyDefault || applyVariations) warn() << "Requested bTag SF, which was not defined in the scale_factors_config: " << name << endl;
    return {{"systematic", 1.0}};
  }

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] =
        TryToEvaluate(name, {extraArgs["systematic"], extraArgs["workingPoint"], stoi(extraArgs["flavour"]), eta, pt});
  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] =
        TryToEvaluate(name, {variation, extraArgs["workingPoint"], stoi(extraArgs["flavour"]), eta, pt});
  }
  return scaleFactors;
}

vector<string> ScaleFactorsManager::GetBTagVariationNames(string name) {
  vector<string> variations;
  if (!ShouldApplyVariation("bTagging")) return variations;

  auto extraArgs = correctionsExtraArgs[name];
  variations = GetScaleFactorVariations(extraArgs["variations"]);
  return variations;
}

map<string, float> ScaleFactorsManager::GetPileupScaleFactor(string name, float nVertices) {
  bool applyDefault = ShouldApplyScaleFactor("pileup");
  bool applyVariations = ShouldApplyVariation("pileup");

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(name, {nVertices, extraArgs["systematic"]});

  if (!applyVariations) return scaleFactors;
  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, {nVertices, variation});
  }
  return scaleFactors;
}

float ScaleFactorsManager::TryToEvaluate(const std::string& name, const vector<std::variant<int, double, std::string>>& args) {
#ifndef USE_CORRECTIONLIB
  return 1.0;
#else
  try {
    return corrections[name]->evaluate(args);
  } catch (std::runtime_error& e) {
    std::string msg = e.what();

    if (msg.find("inputs") != std::string::npos) {
      fatal() << "Expected inputs:\n";
      for (auto corr : corrections[name]->inputs()) fatal() << corr.name() << "\t" << corr.description() << "\n";
      exit(1);
    }

    if (msg.find("bounds") == std::string::npos) {
      fatal() << "Unhandled correctionlib error: " << msg << "\n";
      exit(1);
    }

    auto clampedArgs = args;

    if (!boundsPerInput.count(name)) {
      warn() << "No stored bounds for SF " << name << ". Returning SF=1.\n";
      return 1.0;
    }

    const auto& bounds = boundsPerInput.at(name);
    const auto& inputs = corrections[name]->inputs();

    for (size_t i = 0; i < inputs.size(); ++i) {
      const std::string& varName = inputs[i].name();

      if (!bounds.count(varName)) continue;

      double min = bounds.at(varName).first;
      double max = bounds.at(varName).second;

      if (std::holds_alternative<double>(clampedArgs[i])) {
        double& val = std::get<double>(clampedArgs[i]);

        if (val < min) val = min + 1e-6;
        if (val >= max) val = max - 1e-6;
      }

      // Handle int
      else if (std::holds_alternative<int>(clampedArgs[i])) {
        int& val = std::get<int>(clampedArgs[i]);

        if (val < min) val = static_cast<int>(std::ceil(min));
        if (val >= max) val = static_cast<int>(std::floor(max - 1));
      }
    }

    try {
      return corrections[name]->evaluate(clampedArgs);
    } catch (const std::exception& e2) {
      fatal() << "Clamped evaluation still failed. Original correction: " << name << " Error message: " << e2.what() << endl;
      ;

      fatal() << "After clamp:\n";
      for (size_t j = 0; j < clampedArgs.size(); ++j)
        std::visit([&](auto&& v) { fatal() << "  [" << j << "] = " << v << endl; }, clampedArgs[j]);

      exit(1);
    }
  }
#endif
}

map<string, float> ScaleFactorsManager::GetPileupScaleFactorCustom(int nVertices) {
  bool applyDefault = ShouldApplyScaleFactor("pileup");
  bool applyVariations = ShouldApplyVariation("pileup");

  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else {
    if (nVertices < pileupSFvalues->GetXaxis()->GetBinLowEdge(1)) {
      warn() << "Number of vertices is lower than the lowest bin edge in pileup SF histogram" << endl;
      return scaleFactors;
    }
    if (nVertices > pileupSFvalues->GetXaxis()->GetBinUpEdge(pileupSFvalues->GetNbinsX())) {
      warn() << "Number of vertices is higher than the highest bin edge in pileup SF histogram" << endl;
      return scaleFactors;
    }

    scaleFactors["systematic"] = pileupSFvalues->GetBinContent(pileupSFvalues->FindFixBin(nVertices));
  }

  // if (!applyVariations) return scaleFactors; // No custom variations for pileup SFs?

  return scaleFactors;
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

map<string, pair<double, double>> ScaleFactorsManager::GetInputBounds(map<string, string> extraArgs) {
  map<string, pair<double, double>> inputBounds = {};
  if (!extraArgs.contains("inputBounds")) return inputBounds;
  string bounds_str = extraArgs["inputBounds"];
  istringstream ss(bounds_str);
  string item;

  while (getline(ss, item, ',')) {
    auto sep = item.find(':');
    if (sep == string::npos) continue;
    string key = item.substr(0, sep);
    string rangeStr = item.substr(sep + 1);
    size_t valSep = rangeStr.find(';');
    double minVal = -numeric_limits<double>::infinity();
    double maxVal = numeric_limits<double>::infinity();
    if (valSep != string::npos) {
      string minStr = rangeStr.substr(0, valSep);
      string maxStr = rangeStr.substr(valSep + 1);
      if (!minStr.empty()) minVal = std::stod(minStr);
      if (!maxStr.empty()) maxVal = std::stod(maxStr);
    } else {
      // Only one value provided → treat as max, min=-inf
      maxVal = std::stod(rangeStr);
    }

    if (!inputBounds.count(key)) {
      inputBounds[key] = {minVal, maxVal};
    } else {
      inputBounds[key].first = std::max(inputBounds[key].first, minVal);
      inputBounds[key].second = std::min(inputBounds[key].second, maxVal);
    }
  }
  return inputBounds;
}

map<string, float> ScaleFactorsManager::GetCustomScaleFactorsForCategory(string name, string category) {
  bool applyDefault = ShouldApplyScaleFactor(name);
  bool applyVariations = ShouldApplyVariation(name);

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault) scaleFactors["systematic"] = 1.0;
  // handle empty category - needed to setup the scale factor names for the first event
  else if (category == "")
    scaleFactors["systematic"] = 1.0;
  else
    scaleFactors["systematic"] = TryToEvaluate(name, {category, extraArgs["systematic"]});

  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    if (category == "") {
      scaleFactors[name + "_" + variation] = 1.0;
      continue;
    }
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, {category, variation});
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetCustomScaleFactors(string name, const vector<variant<int, double, string>>& args) {
  bool applyDefault = ShouldApplyScaleFactor(name);
  bool applyVariations = ShouldApplyVariation(name);

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else {
    auto systematic_args = args;
    systematic_args.push_back(extraArgs["systematic"]);
    scaleFactors["systematic"] = TryToEvaluate(name, systematic_args);
  }

  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    auto variation_args = args;
    variation_args.push_back(variation);
    scaleFactors[name + "_" + variation] = TryToEvaluate(name, variation_args);
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetDimuonScaleFactors(string name, const vector<variant<int, double, string>>& args) {
  bool applyDefault = ShouldApplyScaleFactor(name);
  bool applyVariations = ShouldApplyVariation(name);

  map<string, float> scaleFactors;
  auto extraArgs = correctionsExtraArgs[name];
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else {
    auto systematic_args = args;
    systematic_args.push_back(extraArgs["systematic"]);
    scaleFactors["systematic"] = TryToEvaluate(name, systematic_args);
  }

  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs["variations"]);
  for (auto variation : variations) {
    auto variation_args = args;
    variation_args.push_back(variation);
    scaleFactors[name + variation] = TryToEvaluate(name, variation_args);
  }
  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetJetEnergyCorrections(std::map<std::string, float> inputArguments) {
  bool applyDefault = ShouldApplyScaleFactor("jec");
  bool applyVariations = ShouldApplyVariation("jec");

  string name = "jecMC";
  auto extraArgs = correctionsExtraArgs[name];
  map<string, float> scaleFactors;
  if (!applyDefault)
    scaleFactors["systematic"] = 1.0;
  else {
    vector<correction::Variable::Type> inputs;
    for (const correction::Variable& input : compoundCorrections[name]->inputs()) {
      inputs.push_back(inputArguments.at(input.name()));
    }
    scaleFactors["systematic"] = compoundCorrections[name]->evaluate(inputs);
  }
  if (!applyVariations) return scaleFactors;

  vector<string> uncertainties = GetScaleFactorVariations(extraArgs["uncertainties"]);
  for (auto uncertainty : uncertainties) {
    string unc_name = name + "_" + uncertainty;
    vector<correction::Variable::Type> unc_inputs;
    for (const correction::Variable& input : corrections[unc_name]->inputs()) {
      unc_inputs.push_back(inputArguments.at(input.name()));
    }
    float unc = TryToEvaluate(unc_name, unc_inputs);
    scaleFactors[unc_name + "_up"] = 1 + unc;
    scaleFactors[unc_name + "_down"] = 1 - unc;
  }

  return scaleFactors;
}

map<string, float> ScaleFactorsManager::GetJetEnergyResolutionVariables(float jetEta, float jetPt, float rho) {
  bool applyDefault = ShouldApplyScaleFactor("jer");
  bool applyVariations = ShouldApplyVariation("jer");

  string name_sf = "jerMC_ScaleFactor";
  string name_pt = "jerMC_PtResolution";
  auto extraArgs_sf = correctionsExtraArgs[name_sf];
  auto extraArgs_pt = correctionsExtraArgs[name_pt];

  // jer SFs  
  map<string, float> scaleFactors;

  if (!applyDefault) {
    scaleFactors["systematic"] = 1.0;
    scaleFactors["PtResolution"] = 1.0;
  }
  else {
    scaleFactors["systematic"] = TryToEvaluate(corrections[name_sf], {jetEta, extraArgs_sf["systematic"]});
    scaleFactors["PtResolution"] = TryToEvaluate(corrections[name_pt], {jetEta, jetPt, rho});
  }

  if (!applyVariations) return scaleFactors;

  vector<string> variations = GetScaleFactorVariations(extraArgs_sf["variations"]);
  for (auto variation : variations) {
    scaleFactors[name_sf + "_" + variation] = TryToEvaluate(corrections[name_sf], {jetEta, variation});
  }
  return scaleFactors;
}

float ScaleFactorsManager::GetJetEnergyResolutionPt(map<string, variant<int, double, string>> inputArguments) {
  bool applyDefault = ShouldApplyScaleFactor("jer");
  bool applyVariations = ShouldApplyVariation("jer");

  string name = "jerMC_smear";
  auto extraArgs = correctionsExtraArgs[name];
  vector<correction::Variable::Type> inputs;
  for (const correction::Variable& input: corrections[name]->inputs()) {
    inputs.push_back(inputArguments.at(input.name()));
  }
  return corrections[name]->evaluate(inputs);
}

bool ScaleFactorsManager::IsJetVetoMapDefined(string name){
  return (corrections.find(name) != corrections.end());
}
bool ScaleFactorsManager::IsJetVetoMapDefined(string name) { return (corrections.find(name) != corrections.end()); }

bool ScaleFactorsManager::IsJetInBadRegion(string name, float eta, float phi) {
  if (!IsJetVetoMapDefined(name)) {
    error() << "Requested jet veto maps which was not defined in the scale_factors_config: " << name << endl;
    return false;
  }

  float value = TryToEvaluate(name, {"jetvetomap", eta, phi});
  return (value != 0.0);
}
