//  EventReader.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "EventReader.hpp"

#include "Helpers.hpp"

using namespace std;

EventReader::EventReader(string configPath) : currentEvent(make_shared<Event>()) {
  config = make_unique<ConfigManager>(configPath);

  config->GetValue("nEvents", maxEvents);
  config->GetValue("printEveryNevents", printEveryNevents);
  if (printEveryNevents == 0) printEveryNevents = -1;

  string inputFilePath;
  config->GetValue("inputFilePath", inputFilePath);

  inputFile = TFile::Open(inputFilePath.c_str());
  SetupBranches(inputFilePath);
}

EventReader::~EventReader() {}

long long EventReader::GetNevents() const {
  long long nEntries = inputTrees.at("Events")->GetEntries();

  long long nEvents = nEntries;
  if (maxEvents >= 0 && nEvents >= maxEvents) nEvents = maxEvents;

  return nEvents;
}

void EventReader::SetupBranches(string inputPath) {
  vector<string> treeNames = getListOfTrees(inputFile);
  for (string treeName : treeNames) {
    cout << "Loading tree: " << treeName << endl;
    inputTrees[treeName] = (TTree *)inputFile->Get(treeName.c_str());
  }

  auto keysInEventTree = inputTrees["Events"]->GetListOfBranches();
  for (auto i : *keysInEventTree) {
    auto branch = (TBranch *)i;
    string branchName = branch->GetName();
    string branchType = branch->FindLeaf(branchName.c_str())->GetTypeName();
    if (branchType == "") error() << "Couldn't find branch type for branch: " << branchName << "\n";

    bool branchIsVector = false;

    TLeaf *leaf = branch->GetLeaf(branch->GetName());
    if (leaf) {
      branchIsVector = leaf->GetLenStatic() > 1 || leaf->GetLeafCount() != nullptr;
    } else {
      fatal() << "Couldn't get leaf for branch: " << branchName << "\n";
      exit(1);
    }

    if (branchIsVector) {
      SetupVectorBranch(branchName, branchType);
    } else {
      SetupScalarBranch(branchName, branchType);
    }
  }
}

void EventReader::SetupScalarBranch(string branchName, string branchType) {
  currentEvent->valuesTypes[branchName] = branchType;

  if (branchType == "UInt_t") {
    currentEvent->valuesUint[branchName] = 0;
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUint[branchName]);
  } else if (branchType == "Int_t") {
    currentEvent->valuesInt[branchName] = 0;
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesInt[branchName]);
  } else if (branchType == "Bool_t") {
    currentEvent->valuesBool[branchName] = 0;
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesBool[branchName]);
  } else if (branchType == "Float_t") {
    currentEvent->valuesFloat[branchName] = 0;
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesFloat[branchName]);
  } else if (branchType == "ULong64_t") {
    currentEvent->valuesUlong[branchName] = 0;
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUlong[branchName]);
  } else if (branchType == "UChar_t") {
    currentEvent->valuesUchar[branchName] = 0;
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUchar[branchName]);
  } else {
    cout << "ERROR -- unsupported branch type: " << branchType << "\t (branch name: " << branchName << ")" << endl;
  }
}

void EventReader::SetupVectorBranch(string branchName, string branchType) {
  string::size_type pos = branchName.find('_');
  string collectionName = branchName.substr(0, pos);
  string variableName = branchName.substr(pos + 1);

  InitializeCollection(collectionName);

  for (int i = 0; i < maxCollectionElements; i++) {
    currentEvent->collections[collectionName]->at(i)->valuesTypes[variableName] = branchType;
  }

  if (branchType == "Float_t") {
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesFloatVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesFloat[variableName] = &currentEvent->valuesFloatVector[branchName][i];
    }
  } else if (branchType == "UChar_t") {
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesUcharVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesUchar[variableName] = &currentEvent->valuesUcharVector[branchName][i];
    }
  } else if (branchType == "Int_t") {
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesIntVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesInt[variableName] = &currentEvent->valuesIntVector[branchName][i];
    }
  } else if (branchType == "Bool_t") {
    inputTrees["Events"]->SetBranchAddress(branchName.c_str(), &currentEvent->valuesBoolVector[branchName]);
    for (int i = 0; i < maxCollectionElements; i++) {
      currentEvent->collections[collectionName]->at(i)->valuesBool[variableName] = &currentEvent->valuesBoolVector[branchName][i];
    }
  } else {
    cout << "ERROR -- unsupported branch type: " << branchType << "\t (branch name: " << branchName << ")" << endl;
  }
}

void EventReader::InitializeCollection(string collectionName) {
  if (currentEvent->collections.count(collectionName)) return;

  currentEvent->collections[collectionName] = make_shared<PhysicsObjects>();
  for (int i = 0; i < maxCollectionElements; i++) {
    currentEvent->collections[collectionName]->push_back(make_shared<PhysicsObject>(collectionName));
  }
}

shared_ptr<Event> EventReader::GetEvent(int iEvent) {
  if (printEveryNevents > 0) {
    if (iEvent % printEveryNevents == 0) info() << "Event: " << iEvent << endl;
  }

  currentEvent->Reset();

  // Move to desired entry in all trees
  for (auto &[name, tree] : inputTrees) tree->GetEntry(iEvent);

  // Tell collections where to stop in loops, without actually changing their
  // size in memory
  for (auto &[name, collection] : currentEvent->collections) {
    try {
      UInt_t collectionSize = currentEvent->Get("n" + name);
      collection->ChangeVisibleSize(collectionSize);
    } catch (Exception &e) {
      bool workedWithHepMC = true;

      try {
        Int_t collectionSize = currentEvent->Get("Event_numberP");
        collection->ChangeVisibleSize(collectionSize);
      } catch (Exception &e) {
        workedWithHepMC = false;
        if (find(sizeWarningsPrinted.begin(), sizeWarningsPrinted.end(), name) == sizeWarningsPrinted.end()) {
          error() << "Could not set size of collection: " << name << "\n";
          error() << "Range-based loops over this collection should not be used!\n";
          sizeWarningsPrinted.push_back(name);
        }
      }

      if (!workedWithHepMC) {
        if (find(sizeWarningsPrinted.begin(), sizeWarningsPrinted.end(), name) == sizeWarningsPrinted.end()) {
          error() << "Could not set size of collection: " << name << "\n";
          error() << "Range-based loops over this collection should not be used!\n";
          sizeWarningsPrinted.push_back(name);
        }
      }
    }
  }
  return currentEvent;
}
