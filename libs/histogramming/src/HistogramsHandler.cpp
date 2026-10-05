//  HistogramsHandler.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "HistogramsHandler.hpp"

#include <filesystem>

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

HistogramsHandler::HistogramsHandler() {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetHistogramsParams(histParams, "defaultHistParams");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(histParams, "histParams");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(irregularHistParams, "irregularHistParams");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(histParams2D, "histParams2D");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(irregularHistParams2D, "irregularHistParams2D");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(histParams3D, "histParams3D");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(irregularHistParams3D, "irregularHistParams3D");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(profile2DParams, "profile2DParams");
  } catch (const Exception &e) {}

  try {
    config.GetHistogramsParams(irregularProfile2DParams, "irregularProfile2DParams");
  } catch (const Exception &e) {}

  try {
    config.GetValue("histogramsOutputFilePath", outputPath);
  } catch (const Exception &e) {}
  try {
    config.GetVector("SFvariationVariables", SFvariationVariables);
  } catch (const Exception &e) {}

  eventWeights["default"] = 1.0;  // Default weight

  SetupHistograms();
}

HistogramsHandler::~HistogramsHandler() {}

void HistogramsHandler::SetupHistograms() {
  const auto checkProfileCollision = [this](const auto &definitions) {
    for (const auto &[title, params] : definitions) {
      if (profile2DParams.count(title) || irregularProfile2DParams.count(title)) {
        fatal() << "Ambiguous histogram name: " << title << " is configured as both TH3D and TProfile2D" << endl;
        exit(1);
      }
    }
  };
  checkProfileCollision(histParams3D);
  checkProfileCollision(irregularHistParams3D);

  for (auto &[title, params] : histParams) {
    histogramDirectories[title] = params.directory;
    histograms1D[make_pair(title, "")] = new TH1D(title.c_str(), title.c_str(), params.nBins, params.min, params.max);
  }

  for (auto &[title, params] : irregularHistParams) {
    histogramDirectories[title] = params.directory;
    histograms1D[make_pair(title, "")] =
        new TH1D(title.c_str(), title.c_str(), params.binEdges.size() - 1, &params.binEdges[0]);
  }

  for (auto &[title, params] : histParams2D) {
    histogramDirectories[title] = params.directory;
    histograms2D[make_pair(title, "")] = new TH2D(title.c_str(), title.c_str(), params.nBinsX, params.minX, params.maxX,
                                                  params.nBinsY, params.minY, params.maxY);
  }

  for (auto &[title, params] : irregularHistParams2D) {
    histogramDirectories[title] = params.directory;
    histograms2D[make_pair(title, "")] =
        new TH2D(title.c_str(), title.c_str(), params.binEdgesX.size() - 1, &params.binEdgesX[0],
                 params.binEdgesY.size() - 1, &params.binEdgesY[0]);
  }

  for (auto &[title, params] : profile2DParams) {
    histogramDirectories[title] = params.directory;
    profiles2D[make_pair(title, "")] = new TProfile2D(title.c_str(), title.c_str(), params.nBinsX, params.minX,
                                                      params.maxX, params.nBinsY, params.minY, params.maxY);
  }

  for (auto &[title, params] : irregularProfile2DParams) {
    histogramDirectories[title] = params.directory;
    profiles2D[make_pair(title, "")] =
        new TProfile2D(title.c_str(), title.c_str(), params.binEdgesX.size() - 1, params.binEdgesX.data(),
                       params.binEdgesY.size() - 1, params.binEdgesY.data());
  }

  for (auto &[title, params] : histParams3D) {
    histogramDirectories[title] = params.directory;
    histograms3D[make_pair(title, "")] =
        new TH3D(title.c_str(), title.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY,
                 params.maxY, params.nBinsZ, params.minZ, params.maxZ);
  }

  for (auto &[title, params] : irregularHistParams3D) {
    histogramDirectories[title] = params.directory;
    histograms3D[make_pair(title, "")] = new TH3D(
        title.c_str(), title.c_str(), params.binEdgesX.size() - 1, params.binEdgesX.data(), params.binEdgesY.size() - 1,
        params.binEdgesY.data(), params.binEdgesZ.size() - 1, params.binEdgesZ.data());
  }

  // copy names of all histograms to unfilledHistograms vector
  for (auto &[names, hist] : histograms1D) { unfilledHistograms.push_back(names.first); }
  for (auto &[names, hist] : histograms2D) { unfilledHistograms.push_back(names.first); }
  for (auto &[names, hist] : histograms3D) { unfilledHistograms.push_back(names.first); }
  for (auto &[names, profile] : profiles2D) { unfilledHistograms.push_back(names.first); }
}

template <typename THist>
void HistogramsHandler::SetupVariations(map<HistNames, THist *> &histograms) {
  for (auto &[names, histogram] : histograms) {
    if (!names.second.empty() || !histogram ||
        find(SFvariationVariables.begin(), SFvariationVariables.end(), names.first) == SFvariationVariables.end()) {
      continue;
    }
    for (auto &[sfName, weight] : eventWeights) {
      if (sfName == "default") { continue; }
      string title = names.first + "_" + sfName;
      auto *variation = static_cast<THist *>(histogram->Clone(title.c_str()));
      variation->SetTitle(title.c_str());
      // Weights can first be set after nominal fills; variations must start empty.
      variation->Reset();
      histograms[make_pair(names.first, sfName)] = variation;
    }
  }
}

void HistogramsHandler::SetupSFvariationHistograms() {
  SetupVariations(histograms1D);
  SetupVariations(histograms2D);
  SetupVariations(histograms3D);
  SetupVariations(profiles2D);
}

void HistogramsHandler::SetEventWeights(map<string, float> weights) {
  eventWeights = weights;
  if (!sfSetup) {
    SetupSFvariationHistograms();
    sfSetup = true;
  }
};

template <typename THist>
THist *HistogramsHandler::FindHistogram(const map<HistNames, THist *> &histograms, HistNames names, const char *kind) {
  auto it = histograms.find(names);
  if (it == histograms.end() || !it->second) {
    fatal() << "Couldn't find key: " << names.first << ", " << names.second << " in " << kind << " map" << endl;
    exit(1);
  }
  return it->second;
}

template <typename THist, typename... Values>
void HistogramsHandler::FillWeighted(map<HistNames, THist *> &histograms, const char *kind, const string &name,
                                     Values... values) {
  FindHistogram(histograms, {name, ""}, kind)->Fill(values..., eventWeights["default"]);
  RemoveFromUnfilled(name);
  if (find(SFvariationVariables.begin(), SFvariationVariables.end(), name) == SFvariationVariables.end()) { return; }
  for (auto &[sfName, weight] : eventWeights) {
    if (sfName == "default") { continue; }
    FindHistogram(histograms, {name, sfName}, kind)->Fill(values..., weight);
  }
}

void HistogramsHandler::Fill(string name, double value) {
  FillWeighted(histograms1D, "1D histograms", name, value);
}

void HistogramsHandler::Fill(string name, double x, double y) {
  FillWeighted(histograms2D, "2D histograms", name, x, y);
}

void HistogramsHandler::Fill(string name, double x, double y, double zOrProfileValue) {
  if (histograms3D.count({name, ""})) {
    FillWeighted(histograms3D, "3D histograms", name, x, y, zOrProfileValue);
  } else if (profiles2D.count({name, ""})) {
    FillWeighted(profiles2D, "2D profiles", name, x, y, zOrProfileValue);
  } else {
    fatal() << "Couldn't find key: " << name << " in 3D histograms or 2D profiles maps" << endl;
    exit(1);
  }
}

void HistogramsHandler::FillUnweighted(string name, double value) {
  FindHistogram(histograms1D, {name, ""}, "1D histograms")->Fill(value);
  RemoveFromUnfilled(name);
}

void HistogramsHandler::RemoveFromUnfilled(string name) {
  auto it = find(unfilledHistograms.begin(), unfilledHistograms.end(), name);
  if (it != unfilledHistograms.end()) { unfilledHistograms.erase(it); }
}

template <typename THist>
void HistogramsHandler::SaveHistogram(HistNames names, THist *hist, TFile *outputFile) {
  string name = names.first;
  if (!hist) {
    error() << "Histogram " << name << " is null" << endl;
    return;
  }

  auto directoryIt = histogramDirectories.find(name);
  string outputDir = directoryIt == histogramDirectories.end() ? "" : directoryIt->second;
  if (outputDir.empty()) {
    outputFile->cd();
  } else {
    TDirectory *directory = outputFile->GetDirectory(outputDir.c_str());
    if (!directory) { directory = outputFile->mkdir(outputDir.c_str()); }
    if (!directory) {
      error() << "Failed to create histogram output directory: " << outputDir << endl;
      return;
    }
    directory->cd();
  }

  if (hist->GetDimension() >= 2) {
    const double bins = static_cast<double>(hist->GetNbinsX()) * hist->GetNbinsY() *
                        (hist->GetDimension() == 3 ? hist->GetNbinsZ() : 1);
    if (bins > 2000.0 * 2000.0) {
      warn() << "You're creating a very large " << hist->GetDimension() << "D histogram: " << name << " with ";
      warn() << hist->GetNbinsX() << " x " << hist->GetNbinsY();
      if (hist->GetDimension() == 3) { warn() << " x " << hist->GetNbinsZ(); }
      warn() << " bins. This may cause memory issues." << endl;
    }
  }

  hist->Write();
}

void HistogramsHandler::SaveHistograms() {
  const auto separator = outputPath.find_last_of("/");
  string path = separator == string::npos ? "./" : outputPath.substr(0, separator);
  string filename = separator == string::npos ? outputPath : outputPath.substr(separator + 1);
  if (path.empty()) { path = "./"; }
  if (filename.empty()) {
    error() << "Cannot save histograms: output path has no filename: " << outputPath << endl;
    return;
  }
  std::error_code ec;
  std::filesystem::create_directories(path, ec);
  if (ec) { warn() << "Failed to create histogram output directory: " << path << " (" << ec.message() << ")" << endl; }

  auto outputFile = new TFile((path + "/" + filename).c_str(), "recreate");
  outputFile->cd();

  for (auto &[names, hist] : histograms1D) { SaveHistogram(names, hist, outputFile); }
  for (auto &[names, hist] : histograms2D) { SaveHistogram(names, hist, outputFile); }
  for (auto &[names, hist] : histograms3D) { SaveHistogram(names, hist, outputFile); }
  for (auto &[names, profile] : profiles2D) { SaveHistogram(names, profile, outputFile); }

  outputFile->Close();

  // print the output path and filename in nice green color:
  info() << "\033[1;32m" << "Histograms saved to: " << path << "/" << filename << "\033[0m" << endl;
  Print();
}

void HistogramsHandler::Print() {
  for (auto &name : unfilledHistograms) { warn() << "Histogram defined but not filled: " << name << endl; }
}

void HistogramsHandler::SetHistogramLabels(string name, map<int, string> labels) {
  auto hist1DIt = histograms1D.find(make_pair(name, ""));
  if (hist1DIt == histograms1D.end()) {
    error() << "Histogram " << name << " not found for SetHistogramLabels." << endl;
    return;
  }
  for (auto &[bin, label] : labels) { hist1DIt->second->GetXaxis()->SetBinLabel(bin + 1, label.c_str()); }
}
