//  CutFlowManager.cpp
//
//  Created by Jeremi Niedziela on 16/08/2023.

#include "CutFlowManager.hpp"

#include "Helpers.hpp"
#include "Logger.hpp"

using namespace std;

CutFlowManager::CutFlowManager(shared_ptr<EventReader> eventReader_, shared_ptr<EventWriter> eventWriter_)
    : eventReader(eventReader_), eventWriter(eventWriter_), currentIndex(0), inputContainsInitial(false) {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetValue("weightsBranchName", weightsBranchName);
  } catch (const Exception &e) {
    info() << "Weights branch not specified -- will assume weight is 1 for all events" << endl;
  }

  if (eventReader->inputFile->Get("CutFlow")) {
    info() << "Input file contains CutFlow directory - will store existing cutflow in the output." << endl;

    auto sourceDir = (TDirectory *)eventReader->inputFile->Get("CutFlow");

    TIter nextKey(sourceDir->GetListOfKeys());
    TKey *key;

    while ((key = dynamic_cast<TKey *>(nextKey()))) {
      TObject *obj = key->ReadObj();
      auto hist = (TH1D *)obj;
      string cutName = key->GetName();
      float sumOfWeights = hist->GetBinContent(1);
      weightsAfterCuts[cutName] = sumOfWeights;
      if (cutName == "0_initial") inputContainsInitial = true;
      existingCuts.push_back(cutName);
      delete obj;
      currentIndex++;
    }
  }
  if (!eventWriter_) info() << "No eventWriter given for CutFlowManager" << endl;
  
}

CutFlowManager::~CutFlowManager() {}

void CutFlowManager::RegisterCut(string cutName) {
  if (cutName == "initial" && inputContainsInitial) return;
  string fullCutName = (cutName == "initial") ? "0_initial" : (to_string(currentIndex) + "_" + cutName);
  currentIndex++;
  weightsAfterCuts[fullCutName] = 0;
}

string CutFlowManager::GetFullCutName(string cutName) {
  // Find full names in the cut flow matching the given cut name
  vector<string> matchingFullCutNames;
  for (auto &[existingCutName, sumOfWeights] : weightsAfterCuts) {
    if (existingCutName.find(cutName) != string::npos) {
      matchingFullCutNames.push_back(existingCutName);
    }
  }

  // Find the full name with the highest index
  int maxIndex = -1;
  string maxCutName = "";
  for (auto fullCutName : matchingFullCutNames) {
    string number = fullCutName.substr(0, fullCutName.find("_"));
    int index = stoi(number);
    if (index > maxIndex) {
      maxIndex = index;
      maxCutName = fullCutName;
    }
  }
  if (maxCutName != "") return maxCutName;

  // If no matching full name was found, we cannot continue
  fatal() << "CutFlowManager does not contain cut " << cutName << endl;
  fatal() << "Did you forget to register it?" << endl;
  exit(1);
}

float CutFlowManager::GetCurrentEventWeight() {
  float weight = 1.0;
  try {
    weight = eventReader->currentEvent->Get(weightsBranchName);
  } catch (const Exception &e) {
    if (!weightsBranchWarningPrinted) {
      error() << "Could not find weights branch " << weightsBranchName << endl;
      weightsBranchWarningPrinted = true;
    }
  }
  return weight;
}

void CutFlowManager::UpdateCutFlow(string cutName) {
  if (cutName == "initial" && inputContainsInitial) return;
  string fullCutName = GetFullCutName(cutName);
  weightsAfterCuts[fullCutName] += GetCurrentEventWeight();
}

void CutFlowManager::SaveCutFlow() {
  if (!eventWriter) {
    error() << "No existing eventWriter for CutFlowManager - cannot save CutFlow" << endl;
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

std::map<std::string, float> CutFlowManager::GetCutFlow() { return weightsAfterCuts; }

void CutFlowManager::Print() {
  map<int, pair<string, float>> sortedWeightsAfterCuts;
  for (auto &[cutName, sumOfWeights] : weightsAfterCuts) {
    string number = cutName.substr(0, cutName.find("_"));
    int index = stoi(number);
    sortedWeightsAfterCuts[index] = {cutName, sumOfWeights};
  }

  info() << "CutFlow:" << endl;
  for (auto &[index, values] : sortedWeightsAfterCuts) {
    info() << get<0>(values) << " " << get<1>(values) << endl;
  }
}