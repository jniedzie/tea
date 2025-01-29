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

  RegisterPreExistingCutFlows();

  if (!eventWriter_) info() << "No eventWriter given for CutFlowManager" << endl;
}

CutFlowManager::~CutFlowManager() {}

void CutFlowManager::RegisterPreExistingCutFlows() {

  vector<string> existingCutFlows;
  TList *keys = eventReader->inputFile->GetListOfKeys();
  for (int i = 0; i < keys->GetSize(); i++) {
    TKey *key = (TKey*)keys->At(i);
    TString keyName = key->GetName();
    if (keyName.Contains("CutFlow")) existingCutFlows.push_back(keyName.Data());
  }

  for(auto cutFlowName : existingCutFlows) {
    if (!eventReader->inputFile->Get(cutFlowName.c_str())) continue;
    info() << "Input file contains " << cutFlowName << " directory - will store existing cutflow in the output." << endl;

    bool rawEvents = cutFlowName.find("RawEvents")!=string::npos;
    string collectionName = "";
    if(cutFlowName=="CutFlow" || cutFlowName=="RawEventsCutFlow") collectionName = "";
    else if(cutFlowName.find("CollectionCutFlow_")!=string::npos) {
      collectionName = cutFlowName.substr(cutFlowName.find("CollectionCutFlow_")+17);
      if(rawEvents) collectionName = collectionName.substr(collectionName.find("RawEventsCollectionCutFlow_")+26);
    }
    else {
      warn() << "Found cutflow in unknown format: " << cutFlowName << ". Expected cutflow name CutFlow or names starting with CollectionCutFlow_" << endl;
      collectionName = cutFlowName;
    }

    if(!rawEvents && collectionName!="") RegisterCollection(collectionName);
    auto sourceDir = (TDirectory *)eventReader->inputFile->Get(cutFlowName.c_str());

    TIter nextKey(sourceDir->GetListOfKeys());
    TKey *key;

    while ((key = dynamic_cast<TKey *>(nextKey()))) {
      TObject *obj = key->ReadObj();
      auto hist = (TH1D *)obj;
      string cutName = key->GetName();
      float sumOfWeights = hist->GetBinContent(1);
      bool containsInitial = cutName == "0_initial";
      delete obj;

      if(rawEvents) {
        if(collectionName=="") rawEventsAfterCuts[cutName] = sumOfWeights;
        else rawEventsAfterCollectionCuts[collectionName][cutName] = sumOfWeights;
      }
      else {
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
}

void CutFlowManager::RegisterCollection(string collectionName) {
  currentCollectionIndex[collectionName] = 0;
  weightsAfterCollectionCuts[collectionName] = {};
  rawEventsAfterCollectionCuts[collectionName] = {};
  existingCollectionCuts[collectionName] = {};
  inputCollectionContainsInitial[collectionName] = false;
}

void CutFlowManager::RegisterCut(string cutName, string collectionName) {
  if(cutName == "initial" && HasCut("initial", collectionName)) return;
  bool containsInitial = collectionName=="" ? inputContainsInitial : inputCollectionContainsInitial[collectionName];
  if (cutName == "initial" && containsInitial) return;
  int index = collectionName=="" ? currentIndex : currentCollectionIndex[collectionName];
  string fullCutName = (cutName == "initial") ? "0_initial" : (to_string(index) + "_" + cutName);
  if(collectionName=="") {
    currentIndex++;
    weightsAfterCuts[fullCutName] = 0;
    rawEventsAfterCuts[fullCutName] = 0;
  }
  else {
    currentCollectionIndex[collectionName]++;
    weightsAfterCollectionCuts[collectionName][fullCutName] = 0;
    rawEventsAfterCollectionCuts[collectionName][fullCutName] = 0;
  }
}

string CutFlowManager::GetFullCutName(string cutName, string collectionName) {
  // Find full names in the cut flow matching the given cut name
  vector<string> matchingFullCutNames;
  map<string, float> weights = collectionName=="" ? weightsAfterCuts : weightsAfterCollectionCuts[collectionName];
  for (auto &[existingCutName, sumOfWeights] : weights) {
    size_t underscorePos = existingCutName.find("_");
    if (underscorePos != string::npos) {
      string nameAfterUnderscore = existingCutName.substr(underscorePos + 1);
      if (nameAfterUnderscore == cutName) {
        matchingFullCutNames.push_back(existingCutName);
      }
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
      error() << "CutFlowManager failed to get gen weights from branch " << weightsBranchName << endl;
      weightsBranchWarningPrinted = true;
    }
  }
  return weight;
}

void CutFlowManager::UpdateCutFlow(string cutName, string collectionName) {
  bool containsInitial = collectionName=="" ? inputContainsInitial : inputCollectionContainsInitial[collectionName];
  if (cutName == "initial" && containsInitial) return;
  string fullCutName = GetFullCutName(cutName, collectionName);
  if(collectionName=="") {
    weightsAfterCuts[fullCutName] += GetCurrentEventWeight();
    rawEventsAfterCuts[fullCutName] += 1;
  }
  else {
    weightsAfterCollectionCuts[collectionName][fullCutName] += GetCurrentEventWeight();
    rawEventsAfterCollectionCuts[collectionName][fullCutName] += 1;
  }
}

void CutFlowManager::SaveSingleCutFlow(string collectionName) {
  if (!eventWriter) {
    error() << "No existing eventWriter for CutFlowManager - cannot save CutFlow" << endl;
  }
  map<string, float> weights = weightsAfterCuts;
  map<string, float> rawEvents = rawEventsAfterCuts;
  string cutFlowName = "CutFlow";
  if(collectionName!="") {
    cutFlowName = "CollectionCutFlow_"+collectionName;
    weights = weightsAfterCollectionCuts[collectionName];
    rawEvents = rawEventsAfterCollectionCuts[collectionName];
  }
  WriteCutFlow(weights, cutFlowName);
  WriteCutFlow(rawEvents, "RawEvents"+cutFlowName);
}

void CutFlowManager::SaveCutFlow() {
  SaveSingleCutFlow();
  for(auto &[collectionName, vertexCuts] : weightsAfterCollectionCuts){
    SaveSingleCutFlow(collectionName);
  }
}

bool CutFlowManager::HasCut(string cutName, string collectionName) { 
  vector<string> cuts = collectionName=="" ? existingCuts : existingCollectionCuts[collectionName];
  return find(cuts.begin(), cuts.end(), cutName) != cuts.end(); 
}

map<string, float> CutFlowManager::GetCutFlow(string collectionName) { 
  if(collectionName!="") return weightsAfterCollectionCuts[collectionName];
  return weightsAfterCuts; 
}

map<string, float> CutFlowManager::GetRawEventsCutFlow(string collectionName) { 
  if(collectionName!="") return rawEventsAfterCollectionCuts[collectionName];
  return rawEventsAfterCuts; 
}

void CutFlowManager::Print(string collectionName) {
  map<string, float> weights = collectionName=="" ? weightsAfterCuts : weightsAfterCollectionCuts[collectionName];
  map<string, float> rawEvents = collectionName=="" ? rawEventsAfterCuts : rawEventsAfterCollectionCuts[collectionName];
  map<int, pair<string, float>> sortedWeightsAfterCuts;
  map<int, pair<string, float>> sortedRawEventsAfterCuts;
  for (auto &[cutName, sumOfWeights] : weights) {
    string number = cutName.substr(0, cutName.find("_"));
    int index = stoi(number);
    sortedWeightsAfterCuts[index] = {cutName, sumOfWeights};
    sortedRawEventsAfterCuts[index] = {cutName, rawEvents[cutName]};
  }

  info() << "CutFlow (sum of gen weights) (sum of raw events):" << endl;
  for (auto &[index, values] : sortedWeightsAfterCuts) {
    info() << get<0>(values) << " " << get<1>(values) << " " << get<1>(sortedRawEventsAfterCuts[index]) << endl;
  }
}

bool CutFlowManager::isEmpty(string collectionName) { 
  if(collectionName!="") return weightsAfterCollectionCuts[collectionName].empty();
  return weightsAfterCuts.empty(); 
}

bool CutFlowManager::isRawEventsEmpty(string collectionName) { 
  if(collectionName!="") return rawEventsAfterCollectionCuts[collectionName].empty();
  return rawEventsAfterCuts.empty(); 
}

void CutFlowManager::WriteCutFlow(map<string, float> weights, string cutFlowName) {
  eventWriter->outFile->mkdir(cutFlowName.c_str());
  eventWriter->outFile->cd(cutFlowName.c_str());

  for (auto &[cutName, sumOfWeights] : weights) {
    auto hist = new TH1D(cutName.c_str(), cutName.c_str(), 1, 0, 1);
    hist->SetBinContent(1, sumOfWeights);
    hist->Write();
  }
  eventWriter->outFile->cd();
}
