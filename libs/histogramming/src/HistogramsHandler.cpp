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
    config.GetVector("extraSFs", extraSFs);
  } catch (const Exception &e) {
    info() << "Couldn't read extraSFs from config file - no up/down hists will be created" << endl;
  }
  try {
    config.GetHistogramsParams(extraSFsHistParams1D, "extraSFsHistParams1D");
  } catch (const Exception &e) {
    info() << "Couldn't read extraSFsHistParams1D from config file - no 1D up/down hists will be created" << endl;
  }
  try {
    config.GetHistogramsParams(extraSFsHistParams2D, "extraSFsHistParams2D");
  } catch (const Exception &e) {
    info() << "Couldn't read extraSFsHistParams2D from config file - no 2D up/down hists will be created" << endl;
  }

  SetupHistograms();
  SetupExtraSFsHistograms();

}

HistogramsHandler::~HistogramsHandler() {}

void HistogramsHandler::SetupHistograms() {
  for (auto &[title, params] : histParams) {
    histograms1D[title] = new TH1D(title.c_str(), title.c_str(), params.nBins, params.min, params.max);
  }

  for (auto &[title, params] : irregularHistParams) {
    histograms1D[title] = new TH1D(title.c_str(), title.c_str(), params.binEdges.size() - 1, &params.binEdges[0]);
  }

  for (auto &[title, params] : histParams2D) {
    histograms2D[title] =
        new TH2D(title.c_str(), title.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY, params.maxY);
  }
}

void HistogramsHandler::SetupExtraSFsHistograms() {
  for (auto sf : extraSFs) {
    for (auto &[title_, params] : extraSFsHistParams1D) {
      string title = title_ + "_" + sf;
      histograms1Dsf[title] = new TH1D(title.c_str(), title.c_str(), params.nBins, params.min, params.max);
    }
    for (auto &[title_, params] : extraSFsHistParams2D) {
      string title = title_ + "_" + sf;
      histograms2Dsf[title] = 
        new TH2D(title.c_str(), title.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY, params.maxY);
    }
  }
}

void HistogramsHandler::Fill(string name, double value) {
  double weight = eventWeights["central"];
  CheckHistogram(name);
  histograms1D[name]->Fill(value, weight);
  if (extraSFsHistParams1D.find(name) != extraSFsHistParams1D.end()) {
    for (auto sf : extraSFs) {
      weight = eventWeights[sf];
      string namesf = name + "_" + sf;
      CheckExtraSFsHistogram(name);
      histograms1Dsf[namesf]->Fill(value, weight);
    }
  }
}

void HistogramsHandler::Fill(string name, double valueX, double valueY) {
  double weight = eventWeights["central"];
  CheckHistogram(name);
  histograms2D[name]->Fill(valueX, valueY, weight);

  if (extraSFsHistParams2D.find(name) != extraSFsHistParams2D.end()) {
    for (auto sf : extraSFs) {
      weight = eventWeights[sf];
      string namesf = name + "_" + sf;
      CheckExtraSFsHistogram(namesf);
      histograms2Dsf[namesf]->Fill(valueX, valueY, weight);
    }
  }
}

void HistogramsHandler::CheckHistogram(string name) {
  if (!histograms1D.count(name) && !histograms2D.count(name)) {
    fatal() << "Couldn't find key: " << name << " in histograms map" << endl;
    exit(1);
  }
}

void HistogramsHandler::CheckExtraSFsHistogram(string name) {
  if (!histograms1Dsf.count(name) && !histograms2Dsf.count(name)) {
    fatal() << "Couldn't find key: " << name << " in extra SF histograms map" << endl;
    exit(1);
  }
}

template <typename THist>
void HistogramsHandler::SaveHistogram(string name, THist* hist, TFile* outputFile, bool extraSFs) {
  string outputDir = histParams2D[name].directory;
  if (extraSFs) {
    string sfName = name.substr(name.rfind('_') + 1);
    outputDir = outputDir + sfName;
  }
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

  bool emptyHists = false;

  for (auto &[name, hist] : histograms1D) {
    SaveHistogram(name, hist, outputFile);
  }
  for (auto &[name, hist] : histograms1Dsf) {
    SaveHistogram(name, hist, outputFile, true);
  }
  for (auto &[name, hist] : histograms2D) {
    SaveHistogram(name, hist, outputFile);
  }
  for (auto &[name, hist] : histograms2Dsf) {
    SaveHistogram(name, hist, outputFile, true);
  }
  
  outputFile->Close();

  info() << "Histograms saved to: " << path << "/" << filename << endl;

  if (emptyHists) {
    warn() << "Some histograms were defined but never filled -- they will not be stored." << endl;
  }

}
