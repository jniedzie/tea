//  CutFlowManager.cpp
//
//  Created by Jeremi Niedziela on 16/08/2023.

#include "CutFlowManager.hpp"

#include "Helpers.hpp"
#include "Logger.hpp"

using namespace std;

CutFlowManager::CutFlowManager(shared_ptr<EventReader> eventReader_, shared_ptr<EventWriter> eventWriter_, vector<string> additionalCutFlowCollections)
    : eventReader(eventReader_), eventWriter(eventWriter_), currentIndex(0), inputContainsInitial(false) {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetValue("weightsBranchName", weightsBranchName);
  } catch (const Exception &e) {
    info() << "Weights branch not specified -- will assume weight is 1 for all events" << endl;
  }

  RegisterPreExistingCuts();
  for(auto collectionName : additionalCutFlowCollections){
    RegisterCollection(collectionName);
    RegisterPreExistingCuts(collectionName);
  }
  if (!eventWriter_) info() << "No eventWriter given for CutFlowManager" << endl;
}

CutFlowManager::~CutFlowManager() {}

void CutFlowManager::RegisterPreExistingCuts(string collectionName) {
  
  string collectionCutFlowName = collectionName=="" ? "CutFlow" : "CollectionCutFlow_"+collectionName;
  if (eventReader->inputFile->Get(collectionCutFlowName.c_str())) {
    info() << "Input file contains " << collectionCutFlowName << " directory - will store existing cutflow in the output." << endl;

    auto sourceDir = (TDirectory *)eventReader->inputFile->Get(collectionCutFlowName.c_str());

    TIter nextKey(sourceDir->GetListOfKeys());
    TKey *key;

    while ((key = dynamic_cast<TKey *>(nextKey()))) {
      TObject *obj = key->ReadObj();
      auto hist = (TH1D *)obj;
      string cutName = key->GetName();
      float sumOfWeights = hist->GetBinContent(1);
      bool containsInitial = cutName == "0_initial";
      existingCuts.push_back(cutName);
      delete obj;

      if(collectionName=="") {
        weightsAfterCuts[cutName] = sumOfWeights;
        if (containsInitial) inputContainsInitial = true;
        existingCuts.push_back(cutName);
        currentIndex++;
      }
      else {
        weightsAfterCollectionCuts[collectionName][cutName] = sumOfWeights;
        if (containsInitial) inputCollectionContainsInitial[collectionName] = true;
        existingCollectionCuts[collectionName].push_back(cutName);
        currentCollectionIndex[collectionName]++;  
      }    
    }
  }
}

void CutFlowManager::RegisterCollection(string collectionName) {
  currentCollectionIndex[collectionName] = 0;
  weightsAfterCollectionCuts[collectionName] = {};
  existingCollectionCuts[collectionName] = {};
  inputCollectionContainsInitial[collectionName] = false;
}

void CutFlowManager::RegisterCut(string cutName, string collectionName) {
  bool containsInitial = collectionName=="" ? inputContainsInitial : inputCollectionContainsInitial[collectionName];
  if (cutName == "initial" && containsInitial) return;
  int index = collectionName=="" ? currentIndex : currentCollectionIndex[collectionName];
  string fullCutName = (cutName == "initial") ? "0_initial" : (to_string(index) + "_" + cutName);
  if(collectionName=="") {
    currentIndex++;
    weightsAfterCuts[fullCutName] = 0;
  }
  else {
    currentCollectionIndex[collectionName]++;
    weightsAfterCollectionCuts[collectionName][fullCutName] = 0;
  }
}

string CutFlowManager::GetFullCutName(string cutName, string collectionName) {
  // Find full names in the cut flow matching the given cut name
  vector<string> matchingFullCutNames;
  std::map<std::string, float> weights = collectionName=="" ? weightsAfterCuts : weightsAfterCollectionCuts[collectionName];
  for (auto &[existingCutName, sumOfWeights] : weights) {
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
  if (weightsBranchName == "") return weight;

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

void CutFlowManager::UpdateCutFlow(string cutName, string collectionName) {
  bool containsInitial = collectionName=="" ? inputContainsInitial : inputCollectionContainsInitial[collectionName];
  if (cutName == "initial" && containsInitial) return;
  string fullCutName = GetFullCutName(cutName, collectionName);
  weightsAfterCuts[fullCutName] += GetCurrentEventWeight();
  if(collectionName=="") weightsAfterCuts[fullCutName] += GetCurrentEventWeight();
  else weightsAfterCollectionCuts[collectionName][fullCutName] += GetCurrentEventWeight();
}

void CutFlowManager::SaveCutFlow(string collectionName) {
  if (!eventWriter) {
    error() << "No existing eventWriter for CutFlowManager - cannot save CutFlow" << endl;
  }
  std::map<std::string, float> weights = weightsAfterCuts;
  string cutFlowName = "CutFlow";
  if(collectionName!="") {
    cutFlowName = "CollectionCutFlow_"+collectionName;
    weights = weightsAfterCollectionCuts[collectionName];
  }
  eventWriter->outFile->mkdir(cutFlowName.c_str());
  eventWriter->outFile->cd(cutFlowName.c_str());

  for (auto &[cutName, sumOfWeights] : weights) {
    auto hist = new TH1D(cutName.c_str(), cutName.c_str(), 1, 0, 1);
    hist->SetBinContent(1, sumOfWeights);
    hist->Write();
  }
  eventWriter->outFile->cd();
}

void CutFlowManager::SaveAllCutFlows() {
  SaveCutFlow();
  for(auto &[collectionName, vertexCuts] : weightsAfterCollectionCuts){
    SaveCutFlow(collectionName);
  }
}

bool CutFlowManager::HasCut(string cutName, string collectionName) { 
  std::vector<std::string> cuts = collectionName=="" ? existingCuts : existingCollectionCuts[collectionName];
  return std::find(cuts.begin(), cuts.end(), cutName) != cuts.end(); 
}

std::map<std::string, float> CutFlowManager::GetCutFlow(string collectionName) { 
  if(collectionName!="") return weightsAfterCollectionCuts[collectionName];
  return weightsAfterCuts; 
}

void CutFlowManager::Print(string collectionName) {
  std::map<std::string, float> weights = collectionName=="" ? weightsAfterCuts : weightsAfterCollectionCuts[collectionName];
  map<int, pair<string, float>> sortedWeightsAfterCuts;
  for (auto &[cutName, sumOfWeights] : weights) {
    string number = cutName.substr(0, cutName.find("_"));
    int index = stoi(number);
    sortedWeightsAfterCuts[index] = {cutName, sumOfWeights};
  }

  info() << "CutFlow (sum of gen weights):" << endl;
  for (auto &[index, values] : sortedWeightsAfterCuts) {
    info() << get<0>(values) << " " << get<1>(values) << endl;
  }
}
