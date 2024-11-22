//  HistogramsHandler.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "HistogramsHandler.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

HistogramsHandler::HistogramsHandler() {
  auto &config = ConfigManager::GetInstance();

  try{
    config.GetHistogramsParams(histParams, "defaultHistParams");
  }
  catch(const Exception& e){
    info() << "No defaultHistParams found in config file" << endl;
  }

  try{
    config.GetHistogramsParams(histParams, "histParams");
  }
  catch(const Exception& e){
    info() << "No histParams found in config file" << endl;
  }

  try{
    config.GetHistogramsParams(irregularHistParams, "irregularHistParams");
  }
  catch(const Exception& e){
    info() << "No irregularHistParams found in config file" << endl;
  }

  try{
    config.GetHistogramsParams(histParams2D, "histParams2D");
  }
  catch(const Exception& e){
    info() << "No histParams2D found in config file" << endl;
  }

  try{
    config.GetValue("histogramsOutputFilePath", outputPath);
  }
  catch(const Exception& e){
    info() << "No histogramsOutputFilePath found in config file" << endl;
  }

  SetupHistograms();
}

HistogramsHandler::~HistogramsHandler() {}

void HistogramsHandler::SetupHistograms() {
  for (auto &[title, params] : histParams) {
    histograms1D[title] = new TH1D(title.c_str(), title.c_str(), params.nBins, params.min, params.max);
  }

  for (auto &[title, params] : irregularHistParams) {
    histograms1D[title] = new TH1D(title.c_str(), title.c_str(), params.binEdges.size() - 1, &params.binEdges[0]);
  }

  for (auto &[name, params] : histParams2D) {
    histograms2D[name] =
        new TH2D(name.c_str(), name.c_str(), params.nBinsX, params.minX, params.maxX, params.nBinsY, params.minY, params.maxY);
  }
}

void HistogramsHandler::Fill(std::string name, double value, double weight)
{
  CheckHistogram(name);
  histograms1D[name]->Fill(value, weight);
}

void HistogramsHandler::Fill(std::string name, double valueX, double valueY, double weight)
{
  CheckHistogram(name);
  histograms2D[name]->Fill(valueX, valueY, weight);
}

void HistogramsHandler::CheckHistogram(string name){
  if (!histograms1D.count(name) && !histograms2D.count(name)) {
    error() << "Couldn't find key: " << name << " in histograms map"<<endl;
    info() << "Available histograms: " << endl;
    for(auto [histName, hist] : histograms1D) info() << "\t" << histName << endl;
    for(auto [histName, hist] : histograms2D) info() << "\t" << histName << endl;
    exit(1);
  }
}

void HistogramsHandler::SaveHistograms() {
  info() << "Output path: " << outputPath << endl;

  string path = outputPath.substr(0, outputPath.find_last_of("/"));
  string filename = outputPath.substr(outputPath.find_last_of("/"));
  if(path == "") path = "./";
  string command = "mkdir -p " + path;
  system(command.c_str());
  
  auto outputFile = new TFile((path+"/"+filename).c_str(), "recreate");
  outputFile->cd();

  for (auto &[name, hist] : histograms1D) {
    string outputDir = histParams[name].directory;
    if (!outputFile->Get(outputDir.c_str())) outputFile->mkdir(outputDir.c_str());
    outputFile->cd(outputDir.c_str());
    hist->Write();
  }
  for (auto &[name, hist] : histograms2D) {
    string outputDir = histParams2D[name].directory;
    if (!outputFile->Get(outputDir.c_str())) outputFile->mkdir(outputDir.c_str());
    outputFile->cd(outputDir.c_str());
    hist->Write();
  }
  outputFile->Close();

  info() << "Histograms saved to: " << path << "/" << filename << endl;
}
