//  EventReader.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "EventReader.hpp"

#include "Helpers.hpp"

using namespace std;

EventReader::EventReader() {
  auto &config = ConfigManager::GetInstance();

  config.GetVector("eventsTreeNames", eventsTreeNames);
  config.GetMap("specialBranchSizes", specialBranchSizes);

  config.GetValue("nEvents", maxEvents);
  config.GetValue("printEveryNevents", printEveryNevents);
  if (printEveryNevents == 0) printEveryNevents = -1;

  string inputFilePath;
  config.GetValue("inputFilePath", inputFilePath);

  currentEvent = make_shared<Event>();

  // if inputFilePath is a DAS dataset name, insert a redirector into it
  if (inputFilePath.find("root://") == string::npos && inputFilePath.find("/store/") != string::npos) {

    vector<string> redirectors = {
      "xrootd-cms.infn.it",
      "cms-xrd-global.cern.ch",
      "cmsxrootd.fnal.gov",
    };

    string customRedirector = "";
    try {
      config.GetValue("redirector", customRedirector);
    } catch (const Exception &e) {
      info() << "No custom redirector found from config file" << endl;
    }
    if (customRedirector != "") redirectors.insert(redirectors.begin(), customRedirector);

    string tmpInputFilePath;
    for (string redirector : redirectors) {
      info() << "Trying to read ROOT file with redirector:" << redirector << endl;
      tmpInputFilePath = "root://" + redirector + "/" + inputFilePath;
      inputFile = TFile::Open(tmpInputFilePath.c_str());

      if (!inputFile || inputFile->IsZombie()) {
        warn() << "Failed to read ROOT file with redirector: " << redirector << endl;
      } else {
        break;
      }
    }
    if (!inputFile || inputFile->IsZombie()) {
      fatal() << "All redirectors failed" << endl;
      exit(1);
    }
    inputFilePath = tmpInputFilePath;
  } else {
    inputFile = TFile::Open(inputFilePath.c_str());
    if (!inputFile || inputFile->IsZombie()) {
      fatal() << "Local file corrupted: " << inputFilePath << endl;
      exit(1);
    }
  }

  SetupTrees();
  SetupBranches();
}

EventReader::~EventReader() {}

long long EventReader::GetNevents() const {
  long long nEntries = inputTrees.at(eventsTreeNames[0])->GetEntries();

  long long nEvents = nEntries;
  if (maxEvents >= 0 && nEvents >= maxEvents) nEvents = maxEvents;

  return nEvents;
}

tuple<string, string> EventReader::GetCollectionAndVariableNames(string branchName) {
  

  // if collection name is specified in special collections, use that exact name as the collection name
  for(auto &[specialCollectionName, specialBranchSizeName] : specialBranchSizes) {
    auto pos = branchName.find(specialCollectionName);
    
    if (pos != string::npos) {
      auto posEnd = pos + specialCollectionName.size();
      string collectionName = branchName.substr(0, specialCollectionName.size());
      string variableName = branchName.substr(posEnd);
      return make_tuple(collectionName, variableName);
    }
  }

  // otherwise, look for underscores
  string::size_type pos = branchName.find('_');
  string::size_type posEnd = pos + 1;

  // If there's no underscore, the collection and the variable will be called the same
  if (pos == string::npos) return make_tuple(branchName, branchName);
  // TODO: to improve this, we could add a map in the config for custom collection/variable names.
  // E.g. if someone has branches like "MuonPt", MuonEta",... they could define a map like:
  // "MuonPt": ("Muon", "Pt"), "MuonEta": ("Muon", "Eta"),...
  // and if there's some logic to how collection and variable names are formed, 
  // they could generate it automatically in the config.

  // otherwise, cut at the underscore
  string collectionName = branchName.substr(0, pos);
  string variableName = branchName.substr(posEnd);

  return make_tuple(collectionName, variableName);
}

void EventReader::SetupTrees() {
  vector<string> treeNames = getListOfTrees(inputFile);
  for (string treeName : treeNames) {
    if (inputTrees.find(treeName) != inputTrees.end()) continue;

    cout << "Loading tree: " << treeName << endl;
    inputTrees[treeName] = (TTree *)inputFile->Get(treeName.c_str());
  }

  for (string eventsTreeName : eventsTreeNames) {
    if (!inputTrees.count(eventsTreeName)) {
      inputTrees[eventsTreeName] = (TTree *)inputFile->Get(eventsTreeName.c_str());
    }
  }

  for (string eventsTreeName : eventsTreeNames) {
    if (!inputTrees.count(eventsTreeName)) {
      fatal() << "Input file does not contain Events tree" << endl;
      exit(1);
    }
    if (!inputTrees[eventsTreeName]) {
      fatal() << "Couldn't load tree from file: " << eventsTreeName << endl;
      exit(1);
    }
  }
}

TLeaf *EventReader::GetLeaf(TBranch *branch) {
  TLeaf *leaf = nullptr;
  string branchName = branch->GetName();

  if (branch->GetListOfLeaves()->GetEntries() == 1) {
    leaf = (TLeaf *)branch->GetListOfLeaves()->First();
  } else {
    error() << "Branch " << branchName << " has multiple or no leaves." << endl;
  }

  if (!leaf) {
    fatal() << "Couldn't find leaf for branch: " << branchName << endl;
    exit(1);
  }
  return leaf;
}

void EventReader::SetupBranches() {
  for (string eventsTreeName : eventsTreeNames) {
    for (auto branchIter : *inputTrees[eventsTreeName]->GetListOfBranches()) {
      auto branch = (TBranch *)branchIter;
      auto leaf = GetLeaf(branch);

      string branchName = branch->GetName();
      string branchType = leaf->GetTypeName();

      if (branchType == "") error() << "Couldn't find branch type for branch: " << branchName << endl;
      branchNamesAndTypes[branchName] = branchType;

      bool branchIsVector = branchType.find("vector") != string::npos || leaf->GetLenStatic() > 1 || leaf->GetLeafCount() != nullptr;
      if (branchIsVector) {
        SetupVectorBranch(branchName, branchType, eventsTreeName);
      } else {
        SetupScalarBranch(branchName, branchType, eventsTreeName);
      }
    }
  }
}

void EventReader::SetupScalarBranch(string branchName, string branchType, string eventsTreeName) {
  currentEvent->valuesTypes[branchName] = branchType;

  if (branchType == "UInt_t") {
    currentEvent->valuesUint[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUint[branchName]);
  } else if (branchType == "Int_t") {
    currentEvent->valuesInt[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesInt[branchName]);
  } else if (branchType == "Bool_t") {
    currentEvent->valuesBool[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesBool[branchName]);
  } else if (branchType == "Float_t") {
    currentEvent->valuesFloat[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesFloat[branchName]);
  } else if (branchType == "ULong64_t") {
    currentEvent->valuesUlong[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUlong[branchName]);
  } else if (branchType == "UChar_t") {
    currentEvent->valuesUchar[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUchar[branchName]);
  } else if (branchType == "Char_t") {
    currentEvent->valuesChar[branchName] = 0;
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesChar[branchName]);
  } else {
    error() << "unsupported scalar branch type: " << branchType << "\t (branch name: " << branchName << ")" << endl;
  }
}

void EventReader::SetupVectorBranch(string branchName, string branchType, string eventsTreeName) {
  auto [collectionName, variableName] = GetCollectionAndVariableNames(branchName);
  isCollectionAnStdVector[collectionName] = branchType.find("vector") != string::npos;
  InitializeCollection(collectionName);

  for (int i = 0; i < maxCollectionElements; i++) {
    string branchTypeToStore = branchType;
    if (branchType == "vector<float>") branchTypeToStore = "Float_t";
    if (branchType == "vector<int>") branchTypeToStore = "Int_t";
    if (branchType == "vector<unsigned int>") branchTypeToStore = "UInt_t";
    currentEvent->collections[collectionName]->at(i)->valuesTypes[variableName] = branchTypeToStore;
  }

  if (branchType == "Float_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesFloatVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesFloat[variableName] = &currentEvent->valuesFloatVector[branchName][i];
    }
  } else if (branchType == "UChar_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUcharVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesUchar[variableName] = &currentEvent->valuesUcharVector[branchName][i];
    }
  } else if (branchType == "Char_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesCharVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesChar[variableName] = &currentEvent->valuesCharVector[branchName][i];
    }
  } else if (branchType == "Int_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesIntVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesInt[variableName] = &currentEvent->valuesIntVector[branchName][i];
    }
  } else if (branchType == "Bool_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesBoolVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesBool[variableName] = &currentEvent->valuesBoolVector[branchName][i];
    }
  } else if (branchType == "UInt_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUintVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesUint[variableName] = &currentEvent->valuesUintVector[branchName][i];
    }
  } else if (branchType == "UShort_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUshortVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesUshort[variableName] = &currentEvent->valuesUshortVector[branchName][i];
    }
  } else if (branchType == "Short_t") {
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesShortVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesShort[variableName] = &currentEvent->valuesShortVector[branchName][i];
    }
  } else if (branchType == "vector<float>") {
    currentEvent->valuesStdFloatVector[branchName] = new vector<float>(maxCollectionElements, 0);
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesStdFloatVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesFloat[variableName] = &currentEvent->valuesStdFloatVector[branchName]->at(i);
    }
  } else if (branchType == "vector<int>") {
    currentEvent->valuesStdIntVector[branchName] = new vector<int>(maxCollectionElements, 0);
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesStdIntVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesInt[variableName] = &currentEvent->valuesStdIntVector[branchName]->at(i);
    }
  } else if (branchType == "vector<unsigned int>") {
    currentEvent->valuesStdUintVector[branchName] = new vector<unsigned int>(maxCollectionElements, 0);
    inputTrees[eventsTreeName]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesStdUintVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesUint[variableName] = &currentEvent->valuesStdUintVector[branchName]->at(i);
    }
  } else {
    error() << "unsupported vector branch type: " << branchType << "\t (branch name: " << branchName << ")" << endl;
  }
}

void EventReader::InitializeCollection(string collectionName) {
  if (currentEvent->collections.count(collectionName)) return;
  currentEvent->collections[collectionName] = make_shared<PhysicsObjects>();
  for (int i = 0; i < maxCollectionElements; i++) {
    currentEvent->collections[collectionName]->push_back(make_shared<PhysicsObject>(collectionName));
  }
}

template <typename First, typename... Rest>
int EventReader::tryGet(shared_ptr<Event> event, string branchName) {
  try {
    First value = event->Get(branchName);
    return value;
  } catch (BadTypeException &e) {
    if constexpr (sizeof...(Rest) > 0) {
      return tryGet<Rest...>(event, branchName);
    } else {
      return -1;
    }
  }
}

shared_ptr<Event> EventReader::GetEvent(int iEvent) {
  if (printEveryNevents > 0) {
    if (iEvent % printEveryNevents == 0) info() << "Event: " << iEvent << endl;
  }

  currentEvent->Reset();

  // Move to desired entry in all trees
  for (auto &[name, tree] : inputTrees) tree->GetEntry(iEvent);

  // Tell collections where to stop in loops, without actually changing their size in memory
  for (auto &[name, collection] : currentEvent->collections) {
    int collectionSize = -1;

    if (isCollectionAnStdVector[name]) {
      for (auto &[branchName, branchType] : branchNamesAndTypes) {
        auto [collectionName, variableName] = GetCollectionAndVariableNames(branchName);
        if (collectionName != name) continue;

        if (branchType.find("float") != string::npos) {
          collectionSize = currentEvent->valuesStdFloatVector[branchName]->size();
        } else if (branchType.find("unsigned int") != string::npos) {
          collectionSize = currentEvent->valuesStdUintVector[branchName]->size();
        } else if (branchType.find("int") != string::npos) {
          collectionSize = currentEvent->valuesStdIntVector[branchName]->size();
        }
      }
    } else if (specialBranchSizes.count(name)) {
      collectionSize = tryGet<Int_t, UInt_t>(currentEvent, specialBranchSizes[name]);
    } else if (name == "") {
      error() << "Empty collection name. This should never happen, so please report an issue." << endl;
      continue;
    } else {
      collectionSize = tryGet<Int_t, UInt_t>(currentEvent, "n" + name);
    }

    if (collectionSize < 0) {
      error() << "Couldn't determine collection size: " << name << endl;
      continue;
    }
    collection->ChangeVisibleSize(collectionSize);
  }

  currentEvent->AddExtraCollections();
  return currentEvent;
}
