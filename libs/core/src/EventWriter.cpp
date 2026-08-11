//  EventWriter.cpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#include "EventWriter.hpp"

#include <algorithm>

#include "Helpers.hpp"

using namespace std;

namespace {
// Type-code table used both for the leaflist suffix ("F", "I", ...) and to validate that a
// branchesToAdd entry declares one of the nine ROOT scalar types EventWriter knows how to buffer.
const map<string, string> addedBranchTypeCodes = {
    {"Float_t", "F"}, {"Double_t", "D"}, {"Int_t", "I"},     {"UInt_t", "i"},   {"Bool_t", "O"},
    {"ULong64_t", "l"}, {"UChar_t", "b"}, {"Short_t", "S"}, {"UShort_t", "s"},
};

template <typename T>
void FillScalarAddedBranch(map<string, T> &buffer, const string &name, const shared_ptr<Event> &event) {
  if (event->HasCustomValue(name)) {
    try {
      T value = event->Get(name);
      buffer[name] = value;
    } catch (BadTypeException &e) {
      fatal() << "branchesToAdd: event-level branch \"" << name
               << "\" was set with a type that doesn't match its declared branchesToAdd type: " << e.what() << endl;
      exit(1);
    }
  } else {
    buffer[name] = T(0);
    // One event-level branch is set (or not) independently every event, so warning once per branch
    // for the whole job -- rather than once per event -- avoids flooding the log on production runs.
    static set<string> warnedBranches;
    if (warnedBranches.insert(name).second) {
      warn() << "branchesToAdd: event-level branch \"" << name
             << "\" was never set for at least one event, writing default value (further occurrences for this branch won't be logged)"
             << endl;
    }
  }
}

// keepIndices, when non-null, restricts the fill to that subset of the collection (in that order),
// mirroring the reindexing FilterBranch applies to the pre-existing HepMC Particle_* branches so the
// two stay aligned. Returns the number of entries actually written (== collection->size() when
// keepIndices is null).
template <typename T>
size_t FillArrayAddedBranch(T *buffer, const string &variable, size_t previousSize, const shared_ptr<PhysicsObjects> &collection,
                            const vector<int> *keepIndices) {
  static set<string> warnedBranches;

  size_t writeIndex = 0;
  auto fillOne = [&](const shared_ptr<PhysicsObject> &object) {
    T value = T(0);
    if (object->HasCustomValue(variable)) {
      try {
        value = object->Get(variable);
      } catch (BadTypeException &e) {
        fatal() << "branchesToAdd: per-object branch \"" << variable
                 << "\" was set with a type that doesn't match its declared branchesToAdd type: " << e.what() << endl;
        exit(1);
      }
    } else if (warnedBranches.insert(variable).second) {
      warn() << "branchesToAdd: per-object branch \"" << variable
             << "\" was never set for at least one object, writing default value (further occurrences for this branch won't be logged)"
             << endl;
    }
    buffer[writeIndex++] = value;
  };

  if (keepIndices) {
    for (int index : *keepIndices) fillOne(collection->at(index));
  } else {
    for (size_t i = 0; i < collection->size(); i++) fillOne(collection->at(i));
  }
  // Only the shrink remainder needs clearing -- entries already covered by the loop above were
  // just written for real, so re-zeroing them first (as before) was pure duplicated work.
  for (size_t i = writeIndex; i < previousSize; i++) buffer[i] = T(0);
  return writeIndex;
}
}  // namespace

template<typename T>
int FilterBranch(T* vec, const std::vector<int>& keepIndices) {
  T tmp[maxCollectionElements];
  size_t writeIndex = 0;
  for (int i : keepIndices) {
    tmp[writeIndex++] = vec[i];
  }
  for (size_t i = 0; i < maxCollectionElements; ++i) {
    vec[i] = (i < writeIndex) ? tmp[i] : 0;
  }
  return writeIndex;
}

EventWriter::EventWriter(const shared_ptr<EventReader> &eventReader_) : eventReader(eventReader_) {
  auto &config = ConfigManager::GetInstance();
  config.GetValue("treeOutputFilePath", outputFilePath);

  try {
    config.GetVector("branchesToKeep", branchesToKeep);
  } catch (const Exception &e) {
    branchesToKeep = {"*"};  // Keep all branches by default
  }
  try {
    config.GetVector("branchesToRemove", branchesToRemove);
  } catch (const Exception &e) {
    branchesToRemove = {};  // Remove no branches by default
  }

  map<string, vector<string>> branchesToAddConfig;
  try {
    config.GetMap("branchesToAdd", branchesToAddConfig);
  } catch (const Exception &e) {
    branchesToAddConfig = {};  // Add no branches by default
  }
  for (auto &[name, spec] : branchesToAddConfig) {
    if (spec.size() != 2) {
      fatal() << "branchesToAdd entry \"" << name << "\" must be (type, collection)" << endl;
      exit(1);
    }
    AddedBranch added;
    added.type = spec[0];
    added.collection = spec[1];
    if (!added.collection.empty()) {
      string prefix = added.collection + "_";
      if (name.rfind(prefix, 0) != 0) {
        fatal() << "branchesToAdd entry \"" << name << "\" must start with \"" << prefix << "\"" << endl;
        exit(1);
      }
      added.variable = name.substr(prefix.size());
    }
    addedBranches[name] = added;
  }

  SetupOutputTree();
}

EventWriter::~EventWriter() {}

void EventWriter::SetupOutputTree() {
  makeParentDirectories(outputFilePath);

  outFile = new TFile(outputFilePath.c_str(), "recreate");
  outFile->cd();

  for (auto &[name, tree] : eventReader->inputTrees) {
    tree->SetBranchStatus("*", 0);

    for (auto &branchName : branchesToKeep) {
      tree->SetBranchStatus(branchName.c_str(), 1);
    }

    for (auto &branchName : branchesToRemove) {
      tree->SetBranchStatus(branchName.c_str(), 0);
    }

    outputTrees[name] = tree->CloneTree(0);
    outputTrees[name]->Reset();
    SetupBoolVectorBranches(name);

    // Only the events tree(s) carry per-event/per-object custom values; Runs/LuminosityBlocks
    // (and any other auxiliary tree) have no corresponding Event/PhysicsObject state to pull from.
    bool isEventsTree =
        find(eventReader->eventsTreeNames.begin(), eventReader->eventsTreeNames.end(), name) != eventReader->eventsTreeNames.end();
    if (isEventsTree) SetupAddedBranches(name);

    tree->SetBranchStatus("*", 1);
  }
}

void EventWriter::SetupBoolVectorBranches(string treeName) {
  auto outputTree = outputTrees[treeName];

  for (auto branchIter : *outputTree->GetListOfBranches()) {
    auto branch = (TBranch *)branchIter;
    if (!eventReader->IsVectorBranch(branch)) continue;

    auto leaf = eventReader->GetLeaf(branch);
    if (string(leaf->GetTypeName()) != "vector<bool>") continue;

    string branchName = branch->GetName();
    boolVectorBuffers[branchName] = vector<bool>();
    outputTree->SetBranchAddress(branchName.c_str(), &boolVectorBuffers[branchName]);
    boolVectorBranchesPerTree[treeName].push_back(branchName);
  }
}

void EventWriter::RepackBoolVectorBranches(string treeName) {
  auto it = boolVectorBranchesPerTree.find(treeName);
  if (it == boolVectorBranchesPerTree.end()) return;

  auto &event = eventReader->currentEvent;
  for (auto &branchName : it->second) {
    auto *source = event->GetStdUintVector(branchName);
    boolVectorBuffers[branchName].assign(source->begin(), source->end());
  }
}

void EventWriter::SetupAddedBranches(string treeName) {
  auto outputTree = outputTrees[treeName];

  for (auto &[name, added] : addedBranches) {
    if (outputTree->GetBranch(name.c_str())) {
      fatal() << "branchesToAdd: branch \"" << name << "\" already exists on tree " << treeName << endl;
      exit(1);
    }
    auto typeCodeIt = addedBranchTypeCodes.find(added.type);
    if (typeCodeIt == addedBranchTypeCodes.end()) {
      fatal() << "branchesToAdd: unsupported type \"" << added.type << "\" for branch \"" << name << "\"" << endl;
      exit(1);
    }
    string typeCode = typeCodeIt->second;

    if (added.collection.empty()) {
      string leaflist = name + "/" + typeCode;
      if (added.type == "Float_t") outputTree->Branch(name.c_str(), &addedScalarFloat[name], leaflist.c_str());
      else if (added.type == "Double_t") outputTree->Branch(name.c_str(), &addedScalarDouble[name], leaflist.c_str());
      else if (added.type == "Int_t") outputTree->Branch(name.c_str(), &addedScalarInt[name], leaflist.c_str());
      else if (added.type == "UInt_t") outputTree->Branch(name.c_str(), &addedScalarUInt[name], leaflist.c_str());
      else if (added.type == "Bool_t") outputTree->Branch(name.c_str(), &addedScalarBool[name], leaflist.c_str());
      else if (added.type == "ULong64_t") outputTree->Branch(name.c_str(), &addedScalarULong[name], leaflist.c_str());
      else if (added.type == "UChar_t") outputTree->Branch(name.c_str(), &addedScalarUChar[name], leaflist.c_str());
      else if (added.type == "Short_t") outputTree->Branch(name.c_str(), &addedScalarShort[name], leaflist.c_str());
      else if (added.type == "UShort_t") outputTree->Branch(name.c_str(), &addedScalarUShort[name], leaflist.c_str());
      else {
        fatal() << "branchesToAdd: internal error - no scalar branch handler for type \"" << added.type << "\" (branch \"" << name
                << "\"); addedBranchTypeCodes and the type-dispatch chain have drifted apart" << endl;
        exit(1);
      }
    } else {
      try {
        eventReader->currentEvent->GetCollection(added.collection);
      } catch (const Exception &e) {
        fatal() << "branchesToAdd: collection \"" << added.collection << "\" for branch \"" << name << "\" does not exist" << endl;
        exit(1);
      }

      string sizeBranch = eventReader->specialBranchSizes.count(added.collection) ? eventReader->specialBranchSizes[added.collection]
                                                                                   : "n" + added.collection;
      if (!outputTree->GetBranch(sizeBranch.c_str())) {
        fatal() << "branchesToAdd: size branch \"" << sizeBranch << "\" for branch \"" << name << "\" not found on output tree "
                << treeName << " (it may have been pruned by branchesToRemove)" << endl;
        exit(1);
      }
      added.sizeBranch = sizeBranch;

      string leaflist = name + "[" + sizeBranch + "]/" + typeCode;
      if (added.type == "Float_t") outputTree->Branch(name.c_str(), addedVectorFloat[name], leaflist.c_str());
      else if (added.type == "Double_t") outputTree->Branch(name.c_str(), addedVectorDouble[name], leaflist.c_str());
      else if (added.type == "Int_t") outputTree->Branch(name.c_str(), addedVectorInt[name], leaflist.c_str());
      else if (added.type == "UInt_t") outputTree->Branch(name.c_str(), addedVectorUInt[name], leaflist.c_str());
      else if (added.type == "Bool_t") outputTree->Branch(name.c_str(), addedVectorBool[name], leaflist.c_str());
      else if (added.type == "ULong64_t") outputTree->Branch(name.c_str(), addedVectorULong[name], leaflist.c_str());
      else if (added.type == "UChar_t") outputTree->Branch(name.c_str(), addedVectorUChar[name], leaflist.c_str());
      else if (added.type == "Short_t") outputTree->Branch(name.c_str(), addedVectorShort[name], leaflist.c_str());
      else if (added.type == "UShort_t") outputTree->Branch(name.c_str(), addedVectorUShort[name], leaflist.c_str());
      else {
        fatal() << "branchesToAdd: internal error - no array branch handler for type \"" << added.type << "\" (branch \"" << name
                << "\"); addedBranchTypeCodes and the type-dispatch chain have drifted apart" << endl;
        exit(1);
      }
    }

    addedBranchesPerTree[treeName].push_back(name);
  }
}

void EventWriter::FillAddedBranches(string treeName, const vector<int> *keepIndices) {
  auto it = addedBranchesPerTree.find(treeName);
  if (it == addedBranchesPerTree.end()) return;

  auto &event = eventReader->currentEvent;

  for (auto &name : it->second) {
    auto &added = addedBranches.at(name);

    if (added.collection.empty()) {
      if (added.type == "Float_t") FillScalarAddedBranch(addedScalarFloat, name, event);
      else if (added.type == "Double_t") FillScalarAddedBranch(addedScalarDouble, name, event);
      else if (added.type == "Int_t") FillScalarAddedBranch(addedScalarInt, name, event);
      else if (added.type == "UInt_t") FillScalarAddedBranch(addedScalarUInt, name, event);
      else if (added.type == "Bool_t") FillScalarAddedBranch(addedScalarBool, name, event);
      else if (added.type == "ULong64_t") FillScalarAddedBranch(addedScalarULong, name, event);
      else if (added.type == "UChar_t") FillScalarAddedBranch(addedScalarUChar, name, event);
      else if (added.type == "Short_t") FillScalarAddedBranch(addedScalarShort, name, event);
      else if (added.type == "UShort_t") FillScalarAddedBranch(addedScalarUShort, name, event);
      else {
        fatal() << "branchesToAdd: internal error - no scalar fill handler for type \"" << added.type << "\" (branch \"" << name << "\")"
                << endl;
        exit(1);
      }
    } else {
      shared_ptr<PhysicsObjects> collection;
      try {
        collection = event->GetCollection(added.collection);
      } catch (const Exception &e) {
        fatal() << "branchesToAdd: collection \"" << added.collection << "\" for branch \"" << name
                << "\" could not be retrieved for the current event: " << e.what() << endl;
        exit(1);
      }

      // The leaflist declares name[sizeBranch], and sizeBranch is cloned verbatim from the input
      // tree -- unlike collection->size() it is NOT capped at maxCollectionElements, so ROOT would
      // read past our fixed-size buffer at Fill() time if a real event ever exceeds the cap.
      Int_t rawSize = event->GetAs<Int_t>(added.sizeBranch);
      if (rawSize > maxCollectionElements) {
        fatal() << "branchesToAdd: collection \"" << added.collection << "\" has " << rawSize << " elements this event, exceeding "
                << "maxCollectionElements (" << maxCollectionElements << "); cannot safely fill array branch \"" << name << "\"" << endl;
        exit(1);
      }

      size_t previousSize = addedVectorSizes[name];
      const vector<int> *filterIndices = (keepIndices != nullptr && added.collection == "Particle") ? keepIndices : nullptr;
      size_t writeIndex = 0;

      if (added.type == "Float_t") writeIndex = FillArrayAddedBranch(addedVectorFloat[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "Double_t") writeIndex = FillArrayAddedBranch(addedVectorDouble[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "Int_t") writeIndex = FillArrayAddedBranch(addedVectorInt[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "UInt_t") writeIndex = FillArrayAddedBranch(addedVectorUInt[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "Bool_t") writeIndex = FillArrayAddedBranch(addedVectorBool[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "ULong64_t") writeIndex = FillArrayAddedBranch(addedVectorULong[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "UChar_t") writeIndex = FillArrayAddedBranch(addedVectorUChar[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "Short_t") writeIndex = FillArrayAddedBranch(addedVectorShort[name], added.variable, previousSize, collection, filterIndices);
      else if (added.type == "UShort_t") writeIndex = FillArrayAddedBranch(addedVectorUShort[name], added.variable, previousSize, collection, filterIndices);
      else {
        fatal() << "branchesToAdd: internal error - no array fill handler for type \"" << added.type << "\" (branch \"" << name << "\")"
                << endl;
        exit(1);
      }

      addedVectorSizes[name] = writeIndex;
    }
  }
}

void EventWriter::AddCurrentEvent(string treeName) {
  FillAddedBranches(treeName);
  RepackBoolVectorBranches(treeName);
  outputTrees[treeName]->Fill();
}

void EventWriter::AddCurrentHepMCevent(string treeName, const vector<int> &keepIndices) {
  auto &event = eventReader->currentEvent;

  size_t writeIndex;
  for (auto branchIter : *outputTrees[treeName]->GetListOfBranches()) {
    auto branchPtr = (TBranch *)branchIter;

    bool isVectorBranch = eventReader->IsVectorBranch(branchPtr);
    if (!isVectorBranch) continue;

    string branchName = branchPtr->GetName();
    if (branchName.rfind("Particle_", 0) != 0) continue;

    auto leaf = eventReader->GetLeaf(branchPtr);
    string branchType = leaf->GetTypeName();
    

    if (branchType == "Int_t") {
      writeIndex = FilterBranch(event->GetIntVector(branchName), keepIndices);
    } else if (branchType == "Float_t") {
      writeIndex = FilterBranch(event->GetFloatVector(branchName), keepIndices);
    } else if (branchType == "Double_t") {
      writeIndex = FilterBranch(event->GetDoubleVector(branchName), keepIndices);
    } else {
      fatal() << "Unsupported branch type in AddCurrentHepMCevent: " << branchPtr->GetName() << "\ttype: " << leaf->GetTypeName() << endl;
      exit(1);
    }
  }
  // Set the filtered number of particles for the branch before filling
  Int_t nParticles = static_cast<Int_t>(writeIndex);
  outputTrees[treeName]->SetBranchAddress("Event_numberP", &nParticles);
  FillAddedBranches(treeName, &keepIndices);
  RepackBoolVectorBranches(treeName);
  outputTrees[treeName]->Fill();
}

void EventWriter::Save() {
  for (auto &[name, tree] : outputTrees) {
    tree->Write();
  }
  info() << "Saved output trees to " << outputFilePath << endl;
  outFile->Close();
}
