//  HistogramsFiller.cpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#include "HistogramsFiller.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

HistogramsFiller::HistogramsFiller(shared_ptr<HistogramsHandler> histogramsHandler_) : histogramsHandler(histogramsHandler_) {
  auto& config = ConfigManager::GetInstance();

  try {
    config.GetHistogramsParams(defaultHistVariables, "defaultHistParams");
  } catch (const Exception& e) {
    warn() << "Couldn't read defaultHistParams from config file - no default histograms will be included" << endl;
  }

  try {
    config.GetValue("weightsBranchName", weightsBranchName);
  } catch (const Exception& e) {
    info() << "Weights branch not specified -- will assume weight is 1 for all events" << endl;
  }
}

HistogramsFiller::~HistogramsFiller() {}

void HistogramsFiller::FillDefaultVariables(const std::shared_ptr<Event> event) {
  float weight = 1.0;
  try {
    weight = event->Get(weightsBranchName);
  } catch (const Exception &e) {
    warn() << "Coudn't get weight from branch: " << weightsBranchName << endl;
  }

  for (auto& [title, params] : defaultHistVariables) {
    string collectionName = params.collection;
    string branchName = params.variable;

    if (collectionName == "Event") {
      float eventVariable;
      if (branchName[0] == 'n') {
        eventVariable = event->GetCollection(branchName.substr(1))->size();
      } else {
        eventVariable = event->GetAs<float>(branchName);
      }
      histogramsHandler->Fill(title, eventVariable, weight);
    } else {
      auto collection = event->GetCollection(collectionName);
      for (auto object : *collection) {
        histogramsHandler->Fill(title, object->GetAs<float>(branchName), weight);
      }
    }
  }
}

void HistogramsFiller::FillCutFlow(const std::shared_ptr<CutFlowManager> cutFlowManager) {
  int cutFlowLength = cutFlowManager->GetCutFlow().size();
  auto cutFlowHist = new TH1D("cutFlow", "cutFlow", cutFlowLength, 0, cutFlowLength);
  auto rawEventsCutFlowHist = new TH1D("rawEventsCutFlow", "rawEventsCutFlow", cutFlowLength, 0, cutFlowLength);

  map<int, pair<string, float>> sortedWeightsAfterCuts;
  map<int, pair<string, float>> sortedRawEventsAfterCuts;
  auto cutFlow = cutFlowManager->GetCutFlow();
  auto rawEventsCutFlow = cutFlowManager->GetRawEventsCutFlow();
  for (auto& [cutName, sumOfWeights] : cutFlow) {
    string number = cutName.substr(0, cutName.find("_"));
    int index = stoi(number);
    sortedWeightsAfterCuts[index] = {cutName, sumOfWeights};
    sortedRawEventsAfterCuts[index] = {cutName, rawEventsCutFlow[cutName]};
  }

  int bin = 1;
  for (auto& [index, values] : sortedWeightsAfterCuts) {
    cutFlowHist->SetBinContent(bin, get<1>(values));
    rawEventsCutFlowHist->SetBinContent(bin, get<1>(sortedRawEventsAfterCuts[index]));
    cutFlowHist->GetXaxis()->SetBinLabel(bin, get<0>(values).c_str());
    rawEventsCutFlowHist->GetXaxis()->SetBinLabel(bin, get<0>(sortedRawEventsAfterCuts[index]).c_str());
    bin++;
  }
  histogramsHandler->SetHistogram1D("cutFlow", cutFlowHist);
  histogramsHandler->SetHistogram1D("rawEventsCutFlow", rawEventsCutFlowHist);
}
