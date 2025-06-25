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
  config.GetVector("branchesToKeep", branchesToKeep);
  config.GetVector("branchesToRemove", branchesToRemove);

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
