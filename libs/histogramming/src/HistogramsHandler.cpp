//  HistogramsHandler.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "HistogramsHandler.hpp"

#include "ConfigManager.hpp"
#include "EventProcessor.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

HistogramsHandler::HistogramsHandler(string configPath) {
  auto configManager = std::make_unique<ConfigManager>(configPath);
  
  configManager->GetMap("histTitles", histTitles);
  configManager->GetMap("histNbins", histNbins);
  configManager->GetMap("histMin", histMin);
  configManager->GetMap("histMax", histMax);
  configManager->GetMap("histOutputDir", histOutputDir);

  configManager->GetValue("histogramsOutputFilePath", outputPath);
}

HistogramsHandler::~HistogramsHandler() {}

void HistogramsHandler::SetupHistograms() {
  for (auto &[name, title] : histTitles) {
    histograms1D[name] = new TH1D(title.c_str(), title.c_str(), histNbins[name], histMin[name], histMax[name]);
  }
}

void HistogramsHandler::SaveHistograms() {
  auto outputFile = new TFile((outputPath).c_str(), "recreate");
  outputFile->cd();

  for (auto &[name, hist] : histograms1D) {
    string outputDir = histOutputDir[name];
    if (!outputFile->Get(outputDir.c_str())) outputFile->mkdir(outputDir.c_str());
    outputFile->cd(outputDir.c_str());
    hist->Write();
  }
  outputFile->Close();
}