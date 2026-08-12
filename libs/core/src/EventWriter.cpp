//  EventWriter.cpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#include "EventWriter.hpp"

#include <algorithm>

#include "Helpers.hpp"

using namespace std;

namespace {
// The one collection AddCurrentHepMCevent is allowed to prune. Shared by its
// own Particle_* branch-name matching and by FillAddedBranches' decision to
// re-filter an added array branch, so the two can't drift apart the way two
// independent "Particle" literals could.
const string prunedHepMCCollection = "Particle";

template <typename T>
void FillScalarAddedBranch(map<string, T> &buffer, const string &name,
                           const shared_ptr<Event> &event,
                           map<string, bool> &everSetByApp) {
  if (event->HasCustomValue(name)) {
    everSetByApp[name] = true;
    try {
      T value = event->Get(name);
      buffer[name] = value;
    } catch (BadTypeException &e) {
      fatal() << "branchesToAdd: event-level branch \"" << name
              << "\" was set with a type that doesn't match its declared "
                 "branchesToAdd type: "
              << e.what() << endl;
      exit(1);
    }
  } else {
    buffer[name] = T(0);
  }
}

template <typename T>
size_t FillArrayAddedBranch(T *buffer, const string &branchName,
                            const string &variable, size_t previousSize,
                            const shared_ptr<PhysicsObjects> &collection,
                            map<string, bool> &everSetByApp) {
  size_t writeIndex = 0;
  for (auto &object : *collection) {
    T value = T(0);
    if (object->HasCustomValue(variable)) {
      everSetByApp[branchName] = true;
      try {
        value = object->Get(variable);
      } catch (BadTypeException &e) {
        fatal() << "branchesToAdd: per-object branch \"" << variable
                << "\" was set with a type that doesn't match its declared "
                   "branchesToAdd type: "
                << e.what() << endl;
        exit(1);
      }
    }
    buffer[writeIndex++] = value;
  }
  // Only the shrink remainder needs clearing -- entries already covered by the
  // loop above were just written for real, so re-zeroing them first (as before)
  // was pure duplicated work.
  for (size_t i = writeIndex; i < previousSize; i++)
    buffer[i] = T(0);
  return writeIndex;
}
}  // namespace

template <typename T>
int FilterBranch(T *vec, const std::vector<int> &keepIndices) {
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

// Re-applies FilterBranch's compaction to an added array branch that was just
// filled with every object in its collection, when AddCurrentHepMCevent has
// pruned that same collection -- keeping the added branch index-aligned with
// the native Particle_* branches it shares a size leaf with.
template <typename T>
size_t FilterAddedBranchIfPruned(T *buffer, size_t writeIndex,
                                 const string &collectionName,
                                 const vector<int> *keepIndices) {
  if (keepIndices == nullptr || collectionName != prunedHepMCCollection)
    return writeIndex;
  return FilterBranch(buffer, *keepIndices);
}

EventWriter::EventWriter(const shared_ptr<EventReader> &eventReader_)
    : eventReader(eventReader_) {
  auto &config = ConfigManager::GetInstance();
  config.GetValue("treeOutputFilePath", outputFilePath);

  try {
    config.GetVector("branchesToKeep", branchesToKeep);
  } catch (const Exception &e) {
    branchesToKeep = {"*"}; // Keep all branches by default
  }
  try {
    config.GetVector("branchesToRemove", branchesToRemove);
  } catch (const Exception &e) {
    branchesToRemove = {}; // Remove no branches by default
  }

  // branchesToAdd itself was already parsed (and its varexps compiled/validated) by
  // eventReader's AddedBranches; just mirror the specs into our own per-type buffers below.
  for (auto &spec : eventReader->addedBranches->GetSpecs()) {
    AddedBranch added;
    added.type = spec.type;
    added.collection = spec.collection;
    added.variable = spec.name;
    added.hasVarexp = !spec.varexp.empty();
    addedBranches[spec.BranchName()] = added;
    everSetByApp[spec.BranchName()] = false;
  }

  SetupOutputTree();
}

EventWriter::~EventWriter() = default;

void EventWriter::SetupOutputTree() {
  makeParentDirectories(outputFilePath);

  outFile = new TFile(outputFilePath.c_str(), "recreate");
  outFile->cd();

  for (auto &[name, tree] : eventReader->inputTrees) {
    tree->SetBranchStatus("*", false);

    for (auto &branchName : branchesToKeep) {
      tree->SetBranchStatus(branchName.c_str(), true);
    }

    for (auto &branchName : branchesToRemove) {
      tree->SetBranchStatus(branchName.c_str(), false);
    }

    outputTrees[name] = tree->CloneTree(0);
    outputTrees[name]->Reset();
    SetupBoolVectorBranches(name);

    // Only the events tree(s) carry per-event/per-object custom values;
    // Runs/LuminosityBlocks (and any other auxiliary tree) have no
    // corresponding Event/PhysicsObject state to pull from.
    bool isEventsTree = find(eventReader->eventsTreeNames.begin(),
                             eventReader->eventsTreeNames.end(),
                             name) != eventReader->eventsTreeNames.end();
    if (isEventsTree)
      SetupAddedBranches(name);

    tree->SetBranchStatus("*", true);
  }
}

void EventWriter::SetupBoolVectorBranches(string treeName) {
  auto outputTree = outputTrees[treeName];

  for (auto branchIter : *outputTree->GetListOfBranches()) {
    auto branch = (TBranch *)branchIter;
    if (!eventReader->IsVectorBranch(branch))
      continue;

    auto leaf = eventReader->GetLeaf(branch);
    if (string(leaf->GetTypeName()) != "vector<bool>")
      continue;

    string branchName = branch->GetName();
    boolVectorBuffers[branchName] = vector<bool>();
    outputTree->SetBranchAddress(branchName.c_str(),
                                 &boolVectorBuffers[branchName]);
    boolVectorBranchesPerTree[treeName].push_back(branchName);
  }
}

void EventWriter::RepackBoolVectorBranches(string treeName) {
  auto it = boolVectorBranchesPerTree.find(treeName);
  if (it == boolVectorBranchesPerTree.end())
    return;

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
      fatal() << "branchesToAdd: branch \"" << name
              << "\" already exists on tree " << treeName << endl;
      exit(1);
    }
    auto typeCodeIt = kAddedBranchTypeCodes.find(added.type);
    if (typeCodeIt == kAddedBranchTypeCodes.end()) {
      fatal() << "branchesToAdd: unsupported type \"" << added.type
              << "\" for branch \"" << name << "\"" << endl;
      exit(1);
    }
    string typeCode = typeCodeIt->second;

    if (added.collection.empty()) {
      string leaflist = name + "/" + typeCode;
      if (added.type == "Float_t")
        outputTree->Branch(name.c_str(), &addedScalarFloat[name],
                           leaflist.c_str());
      else if (added.type == "Double_t")
        outputTree->Branch(name.c_str(), &addedScalarDouble[name],
                           leaflist.c_str());
      else if (added.type == "Int_t")
        outputTree->Branch(name.c_str(), &addedScalarInt[name],
                           leaflist.c_str());
      else if (added.type == "UInt_t")
        outputTree->Branch(name.c_str(), &addedScalarUInt[name],
                           leaflist.c_str());
      else if (added.type == "Bool_t")
        outputTree->Branch(name.c_str(), &addedScalarBool[name],
                           leaflist.c_str());
      else if (added.type == "ULong64_t")
        outputTree->Branch(name.c_str(), &addedScalarULong[name],
                           leaflist.c_str());
      else if (added.type == "UChar_t")
        outputTree->Branch(name.c_str(), &addedScalarUChar[name],
                           leaflist.c_str());
      else if (added.type == "Short_t")
        outputTree->Branch(name.c_str(), &addedScalarShort[name],
                           leaflist.c_str());
      else if (added.type == "UShort_t")
        outputTree->Branch(name.c_str(), &addedScalarUShort[name],
                           leaflist.c_str());
      else {
        fatal() << "branchesToAdd: internal error - no scalar branch handler "
                   "for type \""
                << added.type << "\" (branch \"" << name
                << "\"); kAddedBranchTypeCodes and the type-dispatch chain have "
                   "drifted apart"
                << endl;
        exit(1);
      }
    } else {
      try {
        eventReader->currentEvent->GetCollection(added.collection);
      } catch (const Exception &e) {
        fatal() << "branchesToAdd: collection \"" << added.collection
                << "\" for branch \"" << name << "\" does not exist" << endl;
        exit(1);
      }

      string sizeBranch =
          eventReader->specialBranchSizes.count(added.collection)
              ? eventReader->specialBranchSizes[added.collection]
              : "n" + added.collection;
      if (!outputTree->GetBranch(sizeBranch.c_str())) {
        fatal() << "branchesToAdd: size branch \"" << sizeBranch
                << "\" for branch \"" << name << "\" not found on output tree "
                << treeName << " (it may have been pruned by branchesToRemove)"
                << endl;
        exit(1);
      }
      added.sizeBranch = sizeBranch;

      string leaflist = name + "[" + sizeBranch + "]/" + typeCode;
      if (added.type == "Float_t")
        outputTree->Branch(name.c_str(), addedVectorFloat[name],
                           leaflist.c_str());
      else if (added.type == "Double_t")
        outputTree->Branch(name.c_str(), addedVectorDouble[name],
                           leaflist.c_str());
      else if (added.type == "Int_t")
        outputTree->Branch(name.c_str(), addedVectorInt[name],
                           leaflist.c_str());
      else if (added.type == "UInt_t")
        outputTree->Branch(name.c_str(), addedVectorUInt[name],
                           leaflist.c_str());
      else if (added.type == "Bool_t")
        outputTree->Branch(name.c_str(), addedVectorBool[name],
                           leaflist.c_str());
      else if (added.type == "ULong64_t")
        outputTree->Branch(name.c_str(), addedVectorULong[name],
                           leaflist.c_str());
      else if (added.type == "UChar_t")
        outputTree->Branch(name.c_str(), addedVectorUChar[name],
                           leaflist.c_str());
      else if (added.type == "Short_t")
        outputTree->Branch(name.c_str(), addedVectorShort[name],
                           leaflist.c_str());
      else if (added.type == "UShort_t")
        outputTree->Branch(name.c_str(), addedVectorUShort[name],
                           leaflist.c_str());
      else {
        fatal() << "branchesToAdd: internal error - no array branch handler "
                   "for type \""
                << added.type << "\" (branch \"" << name
                << "\"); kAddedBranchTypeCodes and the type-dispatch chain have "
                   "drifted apart"
                << endl;
        exit(1);
      }
    }

    addedBranchesPerTree[treeName].push_back(name);
  }
}

void EventWriter::FillAddedBranches(string treeName) {
  auto it = addedBranchesPerTree.find(treeName);
  if (it == addedBranchesPerTree.end())
    return;

  auto &event = eventReader->currentEvent;

  for (auto &name : it->second) {
    auto &added = addedBranches.at(name);

    if (added.collection.empty()) {
      if (added.type == "Float_t")
        FillScalarAddedBranch(addedScalarFloat, name, event, everSetByApp);
      else if (added.type == "Double_t")
        FillScalarAddedBranch(addedScalarDouble, name, event, everSetByApp);
      else if (added.type == "Int_t")
        FillScalarAddedBranch(addedScalarInt, name, event, everSetByApp);
      else if (added.type == "UInt_t")
        FillScalarAddedBranch(addedScalarUInt, name, event, everSetByApp);
      else if (added.type == "Bool_t")
        FillScalarAddedBranch(addedScalarBool, name, event, everSetByApp);
      else if (added.type == "ULong64_t")
        FillScalarAddedBranch(addedScalarULong, name, event, everSetByApp);
      else if (added.type == "UChar_t")
        FillScalarAddedBranch(addedScalarUChar, name, event, everSetByApp);
      else if (added.type == "Short_t")
        FillScalarAddedBranch(addedScalarShort, name, event, everSetByApp);
      else if (added.type == "UShort_t")
        FillScalarAddedBranch(addedScalarUShort, name, event, everSetByApp);
      else {
        fatal() << "branchesToAdd: internal error - no scalar fill handler for "
                   "type \""
                << added.type << "\" (branch \"" << name << "\")" << endl;
        exit(1);
      }
    } else {
      shared_ptr<PhysicsObjects> collection;
      try {
        collection = event->GetCollection(added.collection);
      } catch (const Exception &e) {
        fatal() << "branchesToAdd: collection \"" << added.collection
                << "\" for branch \"" << name
                << "\" could not be retrieved for the current event: "
                << e.what() << endl;
        exit(1);
      }

      // The leaflist declares name[sizeBranch], and sizeBranch is cloned
      // verbatim from the input tree -- unlike collection->size() it is NOT
      // capped at maxCollectionElements, so ROOT would read past our fixed-size
      // buffer at Fill() time if a real event ever exceeds the cap.
      auto rawSize = event->GetAs<Int_t>(added.sizeBranch);
      if (rawSize > maxCollectionElements) {
        fatal() << "branchesToAdd: collection \"" << added.collection
                << "\" has " << rawSize << " elements this event, exceeding "
                << "maxCollectionElements (" << maxCollectionElements
                << "); cannot safely fill array branch \"" << name << "\""
                << endl;
        exit(1);
      }

      size_t previousSize = addedVectorSizes[name];
      size_t writeIndex = 0;

      if (added.type == "Float_t") {
        writeIndex = FillArrayAddedBranch(addedVectorFloat[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorFloat[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "Double_t") {
        writeIndex = FillArrayAddedBranch(addedVectorDouble[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorDouble[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "Int_t") {
        writeIndex = FillArrayAddedBranch(addedVectorInt[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorInt[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "UInt_t") {
        writeIndex = FillArrayAddedBranch(addedVectorUInt[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorUInt[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "Bool_t") {
        writeIndex = FillArrayAddedBranch(addedVectorBool[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorBool[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "ULong64_t") {
        writeIndex = FillArrayAddedBranch(addedVectorULong[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorULong[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "UChar_t") {
        writeIndex = FillArrayAddedBranch(addedVectorUChar[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorUChar[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "Short_t") {
        writeIndex = FillArrayAddedBranch(addedVectorShort[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorShort[name], writeIndex, added.collection,
            currentKeepIndices);
      } else if (added.type == "UShort_t") {
        writeIndex = FillArrayAddedBranch(addedVectorUShort[name], name,
                                          added.variable, previousSize,
                                          collection, everSetByApp);
        writeIndex = FilterAddedBranchIfPruned(
            addedVectorUShort[name], writeIndex, added.collection,
            currentKeepIndices);
      } else {
        fatal() << "branchesToAdd: internal error - no array fill handler for "
                   "type \""
                << added.type << "\" (branch \"" << name << "\")" << endl;
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

void EventWriter::AddCurrentHepMCevent(string treeName,
                                       const vector<int> &keepIndices) {
  auto &event = eventReader->currentEvent;

  size_t writeIndex;
  for (auto branchIter : *outputTrees[treeName]->GetListOfBranches()) {
    auto branchPtr = (TBranch *)branchIter;

    bool isVectorBranch = eventReader->IsVectorBranch(branchPtr);
    if (!isVectorBranch)
      continue;

    string branchName = branchPtr->GetName();
    if (branchName.rfind(prunedHepMCCollection + "_", 0) != 0)
      continue;

    auto leaf = eventReader->GetLeaf(branchPtr);
    string branchType = leaf->GetTypeName();

    if (branchType == "Int_t") {
      writeIndex = FilterBranch(event->GetIntVector(branchName), keepIndices);
    } else if (branchType == "Float_t") {
      writeIndex = FilterBranch(event->GetFloatVector(branchName), keepIndices);
    } else if (branchType == "Double_t") {
      writeIndex =
          FilterBranch(event->GetDoubleVector(branchName), keepIndices);
    } else {
      fatal() << "Unsupported branch type in AddCurrentHepMCevent: "
              << branchPtr->GetName() << "\ttype: " << leaf->GetTypeName()
              << endl;
      exit(1);
    }
  }
  // Set the filtered number of particles for the branch before filling
  Int_t nParticles = static_cast<Int_t>(writeIndex);
  outputTrees[treeName]->SetBranchAddress("Event_numberP", &nParticles);
  currentKeepIndices = &keepIndices;
  FillAddedBranches(treeName);
  currentKeepIndices = nullptr;
  RepackBoolVectorBranches(treeName);
  outputTrees[treeName]->Fill();
}

void EventWriter::Save() {
  // Branches with no varexp are app-set only; if the app never called Set<T> for one across the
  // whole job, every entry silently holds the default value 0 -- worth a single end-of-job flag
  // rather than a per-event warning (which would just be the same message N times over).
  for (auto &[name, added] : addedBranches) {
    if (added.hasVarexp || everSetByApp[name]) continue;
    warn() << "branchesToAdd: branch \"" << name
           << "\" has an empty varexp and was never set by the app for any event; every entry "
              "holds the default value 0"
           << endl;
  }

  for (auto &[name, tree] : outputTrees) {
    tree->Write();
  }
  info() << "Saved output trees to " << outputFilePath << endl;
  outFile->Close();
}
