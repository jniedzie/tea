//  skimmer.cpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#include "ArgsManager.hpp"
#include "ConfigManager.hpp"
#include "CutFlowManager.hpp"
#include "Event.hpp"
#include "EventProcessor.hpp"
#include "EventReader.hpp"
#include "EventWriter.hpp"
#include "ExtensionsHelpers.hpp"
#include "NanoEventProcessor.hpp"

using namespace std;

int main(int argc, char **argv) {
  vector<string> requiredArgs = {"config"};
  vector<string> optionalArgs = {"input_path", "output_trees_path"};
  auto args = make_unique<ArgsManager>(argc, argv, requiredArgs, optionalArgs);
  ConfigManager::Initialize(args);

  auto eventReader = make_shared<EventReader>();
  auto eventWriter = make_shared<EventWriter>(eventReader);
  auto cutFlowManager = make_shared<CutFlowManager>(eventReader, eventWriter);
  auto eventProcessor = make_unique<EventProcessor>();
  auto nanoEventProcessor = make_unique<NanoEventProcessor>();

  cutFlowManager->RegisterCut("initial");
  cutFlowManager->RegisterCut("trigger");
  eventProcessor->RegisterCuts(cutFlowManager);

  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);

    cutFlowManager->UpdateCutFlow("initial");
    if (!eventProcessor->PassesTriggerCuts(event)) { continue; }
    cutFlowManager->UpdateCutFlow("trigger");

    if (!eventProcessor->PassesEventCuts(event, cutFlowManager)) { continue; }

    auto muons = event->GetCollection("Muon");
    if (muons->size() >= 2) {
      auto p1 = muons->at(0)->GetFourVector();
      auto p2 = muons->at(1)->GetFourVector();
      event->Set<float>("dimuonMass", static_cast<float>((p1 + p2).M()));
    }

    vector<float> muonPts;
    for (auto &muon : *muons) { muonPts.push_back(muon->GetAs<float>("pt")); }
    event->SetVector<float>("muonPt", muonPts);

    // Branches declared without a varexp are only filled where the app sets them, and get a default
    // value (zero) everywhere else - both for objects skipped here and for entire events skipped below
    for (auto &muon : *muons) {
      float pt = muon->GetAs<float>("pt");
      if (pt > 30) { muon->Set<float>("ptIfGood", pt); }
    }

    eventWriter->AddCurrentEvent("Events");
  }
  cutFlowManager->SaveCutFlow();
  cutFlowManager->Print();
  eventWriter->Save();

  return 0;
}
