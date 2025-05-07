//  HistogramsHandler.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "HistogramsHandler.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

HistogramsHandler::HistogramsHandler() {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetHistogramsParams(histParams, "defaultHistParams");
  } catch (const Exception &e) {
    info() << "No defaultHistParams found in config file" << endl;
  }

  try {
    config.GetHistogramsParams(histParams, "histParams");
  } catch (const Exception &e) {
    info() << "No histParams found in config file" << endl;
  }

  try {
    config.GetHistogramsParams(irregularHistParams, "irregularHistParams");
  } catch (const Exception &e) {
    info() << "No irregularHistParams found in config file" << endl;
  }

  try {
    config.GetHistogramsParams(histParams2D, "histParams2D");
  } catch (const Exception &e) {
    info() << "No histParams2D found in config file" << endl;
  }

  try {
    config.GetValue("histogramsOutputFilePath", outputPath);
  } catch (const Exception &e) {
    info() << "No histogramsOutputFilePath found in config file" << endl;
  }
  try {
    config.GetVector("SFvariationVariables", SFvariationVariables);
  } catch (const Exception &e) {
    info() << "Couldn't read SFvariationVariables from config file - no up/down hists will be created" << endl;
  }

  SetupHistograms();

}

HistogramsHandler::~HistogramsHandler() {}

void HistogramsHandler::SetupHistograms() {
  for (auto &[title, params] : histParams) {
    histograms1D[make_pair(title, "")] = new TH1D(title.c_str(), title.c_str(), params.nBins, params.min, params.max);
  }

  for (auto &[title, params] : irregularHistParams) {
    histograms1D[make_pair(title, "")] = new TH1D(title.c_str(), title.c_str(), params.binEdges.size() - 1, &params.binEdges[0]);
  }

  for (auto &[title, params] : histParams2D) {
    histograms2D[make_pair(title, "")] =
        new TH2D(title.c_str(), title.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY, params.maxY);
  }
}

void HistogramsHandler::SetupSFvariationHistograms() {
  for (auto &[title, params] : histParams) {
    if (find(SFvariationVariables.begin(), SFvariationVariables.end(), title) ==  SFvariationVariables.end()) continue;
    for (auto &[sfName, weight] : eventWeights) {
      if (sfName == "default") continue;
      string titlesf = title + "_" + sfName;
      histograms1D[make_pair(title, sfName)] = new TH1D(titlesf.c_str(), titlesf.c_str(), params.nBins, params.min, params.max);
    }
  }

  for (auto &[title, params] : irregularHistParams) {
    if (find(SFvariationVariables.begin(), SFvariationVariables.end(), title) ==  SFvariationVariables.end()) continue;    
    for (auto &[sfName, weight] : eventWeights) {
      if (sfName == "default") continue;
      string titlesf = title + "_" + sfName;
      histograms1D[make_pair(title, sfName)] = new TH1D(titlesf.c_str(), titlesf.c_str(), params.binEdges.size() - 1, &params.binEdges[0]);
    }
  }

  for (auto &[title, params] : histParams2D) {
    if (find(SFvariationVariables.begin(), SFvariationVariables.end(), title) ==  SFvariationVariables.end()) continue;
    for (auto &[sfName, weight] : eventWeights) {
      if (sfName == "default") continue;
      string titlesf = title + "_" + sfName;
      histograms2D[make_pair(title, sfName)] = 
          new TH2D(titlesf.c_str(), titlesf.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY, params.maxY);
    }
  }
}

void HistogramsHandler::SetEventWeights(map<string,float> weights) { 
  bool firstIteration = eventWeights.empty() ? true : false;
  eventWeights = weights; 
  if (firstIteration) SetupSFvariationHistograms();
};

void HistogramsHandler::Fill(string name, double value) {
  double weight = eventWeights["default"];
  CheckHistogram(name, "");
  histograms1D[make_pair(name, "")]->Fill(value, weight);
  if (find(SFvariationVariables.begin(), SFvariationVariables.end(), name) ==  SFvariationVariables.end()) return;
  for (auto &[sfName, weight] : eventWeights) {
    if (sfName == "default") continue;
    CheckHistogram(name, sfName);
    histograms1D[make_pair(name, sfName)]->Fill(value, weight);
  }
}

void HistogramsHandler::Fill(string name, double valueX, double valueY) {
  double weight = eventWeights["default"];
  CheckHistogram(name, "");
  histograms2D[make_pair(name, "")]->Fill(valueX, valueY, weight);
  if (find(SFvariationVariables.begin(), SFvariationVariables.end(), name) ==  SFvariationVariables.end()) return;
  for (auto &[sfName, weight] : eventWeights) {
    if (sfName == "default") continue;
    CheckHistogram(name, sfName);
    histograms2D[make_pair(name, sfName)]->Fill(valueX, valueY, weight);
  }
}

void HistogramsHandler::CheckHistogram(string name, string directory) {
  if (!histograms1D.count(make_pair(name,directory)) && !histograms2D.count(make_pair(name,directory))) {
    fatal() << "Couldn't find key: " << name << ", " << directory << " in histograms map" << endl;
    exit(1);
  }
}

template <typename THist>
void HistogramsHandler::SaveHistogram(HistNames names, THist* hist, TFile* outputFile) {
  string name = names.first;
  string outputDir = names.second;  
  if (!outputFile->Get(outputDir.c_str())) outputFile->mkdir(outputDir.c_str());

  outputFile->cd(outputDir.c_str());
  if (!hist) {
    error() << "Histogram " << name << " is null" << endl;
    return;
  }
  if constexpr (std::is_same<THist, TH2D>::value) {
    if (hist->GetNbinsX() * hist->GetNbinsY() > 2000 * 2000) {
      warn() << "You're creating a very large 2D histogram: " << name << " with ";
      warn() << hist->GetNbinsX() << " x " << hist->GetNbinsY() << " bins. ";
      warn() << "This may cause memory issues." << endl;
    }
  }

  hist->Write();
}

void HistogramsHandler::SaveHistograms() {
  info() << "Output path: " << outputPath << endl;

  string path = outputPath.substr(0, outputPath.find_last_of("/"));
  string filename = outputPath.substr(outputPath.find_last_of("/"));
  if (path == "") path = "./";
  string command = "mkdir -p " + path;
  system(command.c_str());

  auto outputFile = new TFile((path + "/" + filename).c_str(), "recreate");
  outputFile->cd();

  for (auto &[names, hist] : histograms1D) {
    SaveHistogram(names, hist, outputFile);
  }
  for (auto &[names, hist] : histograms2D) {
    SaveHistogram(names, hist, outputFile);
  }
  
  outputFile->Close();

  info() << "Histograms saved to: " << path << "/" << filename << endl;

}
