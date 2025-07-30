//  EventWriter.cpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#include "EventWriter.hpp"

#include "Helpers.hpp"

using namespace std;

EventWriter::EventWriter(const std::shared_ptr<EventReader> &eventReader_) : eventReader(eventReader_) {
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

void EventWriter::Save() {
  for (auto &[name, tree] : outputTrees) {
    tree->Write();
  }
  outFile->Close();
}
