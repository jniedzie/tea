//  skimmer.cpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#include "ConfigManager.hpp"
#include "Event.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"
#include "EventWriter.hpp"
#include "CutFlowManager.hpp"
#include "EventProcessor.hpp"
#include "NanoEventProcessor.hpp"
#include "ArgsManager.hpp"

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
    if(!eventProcessor->PassesTriggerCuts(event)) continue;
    cutFlowManager->UpdateCutFlow("trigger");

    if(!eventProcessor->PassesEventCuts(event, cutFlowManager)) continue;

    // Demonstrate branchesToAdd: an event-level scalar and a per-object array branch.
    auto muons = event->GetCollection("Muon");
    if (muons->size() >= 2) {
      auto p1 = muons->at(0)->GetFourVector();
      auto p2 = muons->at(1)->GetFourVector();
      event->SetFloat("dimuonMass", static_cast<float>((p1 + p2).M()));
    } else {
      event->SetFloat("dimuonMass", -1.f);
    }
    for (auto muon : *muons) {
      float pt = muon->GetAs<float>("pt");
      muon->SetFloat("ptSquared", pt * pt);
    }

    eventWriter->AddCurrentEvent("Events");
  }
  cutFlowManager->SaveCutFlow();
  cutFlowManager->Print();
  eventWriter->Save();

  return 0;
}
