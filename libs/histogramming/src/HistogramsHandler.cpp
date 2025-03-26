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
    config.GetVector("scaleFactorTypes", scaleFactorTypes);
  } catch (const Exception &e) {
    info() << "Couldn't read scaleFactorTypes from config file - will only use ['central'] SF" << endl;
    scaleFactorTypes = {"central"};
  }

  SetupHistograms();
}

HistogramsHandler::~HistogramsHandler() {}

void HistogramsHandler::SetupHistograms() {
  for (auto sfType : scaleFactorTypes) {
    string sfName = "";
      if (sfType != "central") sfName = "_"+sfType;
    for (auto &[title_, params] : histParams) {
      string title = title_ + sfName;
      histograms1D[title] = new TH1D(title.c_str(), title.c_str(), params.nBins, params.min, params.max);
    }

    for (auto &[title_, params] : irregularHistParams) {
      string title = title_ + sfName;
      histograms1D[title] = new TH1D(title.c_str(), title.c_str(), params.binEdges.size() - 1, &params.binEdges[0]);
    }

    for (auto &[title_, params] : histParams2D) {
      string title = title_ + sfName;
      histograms2D[title] =
          new TH2D(title.c_str(), title.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY, params.maxY);
    }
  }
}

void HistogramsHandler::Fill(string name, double value) {
  for (auto sfType : scaleFactorTypes) {
    if (sfType != "central") name = name + "_"+sfType;
    double weight = eventWeights[sfType];
    CheckHistogram(name);
    histograms1D[name]->Fill(value, weight);
  }
}

void HistogramsHandler::Fill(string name, double valueX, double valueY) {
  for (auto sfType : scaleFactorTypes) {
    if (sfType != "central") name = name + "_"+sfType;
    double weight = eventWeights[sfType];
    CheckHistogram(name);
    histograms2D[name]->Fill(valueX, valueY, weight);
  }
}

void HistogramsHandler::CheckHistogram(string name) {
  if (!histograms1D.count(name) && !histograms2D.count(name)) {
    fatal() << "Couldn't find key: " << name << " in histograms map" << endl;
    exit(1);
  }
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

  for (auto sfType : scaleFactorTypes) {
    string sfName = "";
    if (sfType != "central") sfName = "_"+sfType;
    for (auto &[name_, hist] : histograms1D) {
      string name = name_ + sfName;
      string outputDir = histParams[name].directory;
      if (!outputFile->Get(outputDir.c_str())) outputFile->mkdir(outputDir.c_str());

      if (hist->GetEntries() == 0) {
        emptyHists = true;
        continue;
      }

      outputFile->cd(outputDir.c_str());
      hist->Write();
    }
    for (auto &[name_, hist] : histograms2D) {
      string name = name_ + sfName;
      string outputDir = histParams2D[name].directory;
      if (!outputFile->Get(outputDir.c_str())) outputFile->mkdir(outputDir.c_str());

      if (hist->GetEntries() == 0) {
        emptyHists = true;
        continue;
      }

      outputFile->cd(outputDir.c_str());
      if (!hist) {
        error() << "Histogram " << name << " is null" << endl;
        continue;
      }
      if (hist->GetNbinsX() * hist->GetNbinsY() > 2000 * 2000) {
        warn() << "You're creating a very large 2D histogram: " << name << " with ";
        warn() << hist->GetNbinsX() << " x " << hist->GetNbinsY() << " bins. ";
        warn() << "This may cause memory issues." << endl;
      }

      hist->Write();
    }
  }
  outputFile->Close();

  info() << "Histograms saved to: " << path << "/" << filename << endl;

  if (emptyHists) {
    warn() << "Some histograms were defined but never filled -- they will not be stored." << endl;
  }

}
