//  EventWriter.cpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#include "EventWriter.hpp"

#include "Helpers.hpp"

using namespace std;

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

void EventWriter::AddCurrentEvent(string treeName) {
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
