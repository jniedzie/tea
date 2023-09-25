//  EventWriter.cpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#include "EventWriter.hpp"

#include "Helpers.hpp"

using namespace std;

EventWriter::EventWriter(string configPath, const std::shared_ptr<EventReader> &eventReader_) : eventReader(eventReader_) {
  config = make_unique<ConfigManager>(configPath);

  string outputFilePath;
  config->GetValue("treeOutputFilePath", outputFilePath);

  SetupOutputTree(outputFilePath);
}

EventWriter::~EventWriter() {}

void EventWriter::SetupOutputTree(string outFileName) {
  makeParentDirectories(outFileName);

  outFile = new TFile(outFileName.c_str(), "recreate");
  outFile->cd();

  for (auto &[name, tree] : eventReader->inputTrees) {
    outputTrees[name] = tree->CloneTree(0);
    outputTrees[name]->Reset();
  }
}

void EventWriter::AddCurrentEvent(string treeName) { outputTrees[treeName]->Fill(); }

void EventWriter::Save() {
  for (auto &[name, tree] : outputTrees) {
    tree->Write();
  }
  outFile->Close();
}
