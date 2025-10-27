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
  string outputFilePath;
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

  SetupOutputTree(outputFilePath);
}

EventWriter::~EventWriter() {}

void EventWriter::SetupOutputTree(string outFileName) {
  makeParentDirectories(outFileName);

  outFile = new TFile(outFileName.c_str(), "recreate");
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

    tree->SetBranchStatus("*", 1);
  }
}

void EventWriter::AddCurrentEvent(string treeName) { outputTrees[treeName]->Fill(); }

void EventWriter::AddCurrentHepMCevent(string treeName, const vector<int> &keepIndices) {
  auto &event = eventReader->currentEvent;

  size_t writeIndex;
  for (auto branchIter : *outputTrees[treeName]->GetListOfBranches()) {
    auto branchPtr = (TBranch *)branchIter;

    bool isVectorBranch = eventReader->IsVectorBranch(branchPtr);
    if (!isVectorBranch) continue;

    string branchName = branchPtr->GetName();
    if (!branchName.starts_with("Particle_")) continue;

    auto leaf = eventReader->GetLeaf(branchPtr);
    string branchType = leaf->GetTypeName();
    

    if (branchType == "Int_t") {
      writeIndex = FilterBranch(event->GetIntVector(branchName), keepIndices);
    } else if (branchType == "Float_t") {
      writeIndex = FilterBranch(event->GetFloatVector(branchName), keepIndices);
    } else {
      fatal() << "Unsupported branch type in AddCurrentEvent: " << branchPtr->GetName() << "\ttype: " << leaf->GetTypeName() << endl;
      exit(0);
    }
  }
  // Set the filtered number of particles for the branch before filling
  Int_t nParticles = static_cast<Int_t>(writeIndex);
  outputTrees[treeName]->SetBranchAddress("Event_numberP", &nParticles);
  outputTrees[treeName]->Fill();
}

void EventWriter::Save() {
  for (auto &[name, tree] : outputTrees) {
    tree->Write();
  }
  outFile->Close();
}
