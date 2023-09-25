//  CutFlowManager.cpp
//
//  Created by Jeremi Niedziela on 16/08/2023.

#include "CutFlowManager.hpp"

#include "Helpers.hpp"
#include "Logger.hpp"

using namespace std;

CutFlowManager::CutFlowManager(shared_ptr<EventReader> eventReader_, shared_ptr<EventWriter> eventWriter_)
    : eventReader(eventReader_), eventWriter(eventWriter_), currentIndex(0) {
  if (eventReader->inputFile->Get("CutFlow")) {
    info() << "Input file contains CutFlow directory - will store existing cutflow for output.\n";

    auto sourceDir = (TDirectory *)eventReader->inputFile->Get("CutFlow");

    TIter nextKey(sourceDir->GetListOfKeys());
    TKey *key;

    while ((key = dynamic_cast<TKey *>(nextKey()))) {
      TObject *obj = key->ReadObj();
      auto hist = (TH1D*)obj;
      weightsAfterCuts[key->GetName()] = hist->GetBinContent(1);
      delete obj;
      currentIndex++;
    }
  }
  if(!eventWriter_) {
    info() << "No eventWriter given for CutFlowManager\n";
  }
}

CutFlowManager::~CutFlowManager() {}

void CutFlowManager::UpdateCutFlow(string cutName) {
  float weight = 1;

  string fullCutName;

  bool found = false;
  for (const auto &[key, value] : weightsAfterCuts) {
    if (key.find(cutName) != std::string::npos) {
      fullCutName = key;
      found = true;
      break;
    }
  }
  if(!found){
    fullCutName = to_string(currentIndex) + "_" + cutName;
  }

  try {
    eventReader->currentEvent->Get("genWeight");
  } catch (Exception &) {
  }

  if (weightsAfterCuts.count(fullCutName)) {
    weightsAfterCuts[fullCutName] += weight;
  } else {
    weightsAfterCuts[fullCutName] = weight;
    currentIndex++;
  }
}

void CutFlowManager::SaveCutFlow() {
  if (!eventWriter) {
    error() << "Error: No existing eventWriter for CutFlowManager - cannot save CutFlow\n";
  }
  if (!eventReader->inputFile->Get("CutFlow")) {
    info() << "Input file doesn't contain CutFlow directory yet... will create a new one in the output file.\n";
    eventWriter->outFile->mkdir("CutFlow");
  } 
  eventWriter->outFile->mkdir("CutFlow");
  eventWriter->outFile->cd("CutFlow");

  for (auto &[cutName, sumOfWeights] : weightsAfterCuts) {
    auto hist = new TH1D(cutName.c_str(), cutName.c_str(), 1, 0, 1);
    hist->SetBinContent(1, sumOfWeights);
    hist->Write();
  }
  eventWriter->outFile->cd();
}


std::map<std::string, float> CutFlowManager::GetCutFlow() {
  return weightsAfterCuts;
}
