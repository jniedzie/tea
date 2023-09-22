//  HistogramsFiller.cpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#include "HistogramsFiller.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

HistogramsFiller::HistogramsFiller(string configPath, shared_ptr<HistogramsHandler> histogramsHandler_)
    : histogramsHandler(histogramsHandler_) {
  auto configManager = std::make_unique<ConfigManager>(configPath);

  eventProcessor = make_unique<EventProcessor>();

  try {
    configManager->GetMap("defaultHistVariables", defaultHistVariables);
  }
  catch (const Exception& e){
    warn() << "Couldn't read defaultHistVariables from config file - no default histograms will be included";
  }

}

HistogramsFiller::~HistogramsFiller() {}


void HistogramsFiller::FillDefaultVariables(const std::shared_ptr<Event> event) {
  for(auto &[histName, variableLocation] : defaultHistVariables) {
    if(variableLocation[0] == "Event") {
      // Assuming uint nObject from Event for now
      uint eventVariable = event->Get(variableLocation[1]);
      histogramsHandler->histograms1D[histName]->Fill(eventVariable);
    } else {
      auto collection = event->GetCollection(variableLocation[0]);
      for(auto object : *collection){
        histogramsHandler->histograms1D[histName]->Fill(object->Get(variableLocation[1]));
      }
    }
  }
}


void HistogramsFiller::FillCutFlow(const std::shared_ptr<CutFlowManager> cutFlowManager) {
  int bin = 1;
  int cutFlowLength = cutFlowManager->GetCutFlow().size();
  TH1D* cutFlowHist = new TH1D("cutFlow", "cutFlow", cutFlowLength, 0, cutFlowLength+1);
  for(auto &[name, weight] : cutFlowManager->GetCutFlow()){
    cutFlowHist->SetBinContent(bin, weight);
    cutFlowHist->GetXaxis()->SetBinLabel(bin, name.c_str());
    bin++;
  }
  histogramsHandler->histograms1D["cutFlow"] = cutFlowHist;
}
