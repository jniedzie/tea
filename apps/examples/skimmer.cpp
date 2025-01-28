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
#include "ArgsManager.hpp"

using namespace std;

int main(int argc, char **argv) {
  auto args = make_unique<ArgsManager>(argc, argv);
  if (!args->GetString("config").has_value()) {
    fatal() << "No config file provided" << endl;
    exit(1);
  }

  ConfigManager::Initialize(args->GetString("config").value());
  auto &config = ConfigManager::GetInstance();
  
  if (args->GetString("input_path").has_value()) {
    config.SetInputPath(args->GetString("input_path").value());
  }
  if (args->GetString("output_trees_path").has_value()) {
    config.SetTreesOutputPath(args->GetString("output_trees_path").value());
  }

  auto eventReader = make_shared<EventReader>();
  auto eventWriter = make_shared<EventWriter>(eventReader);
  auto cutFlowManager = make_shared<CutFlowManager>(eventReader, eventWriter);
  auto eventProcessor = make_unique<EventProcessor>();
  
  cutFlowManager->RegisterCut("initial");
  cutFlowManager->RegisterCut("trigger");
  eventProcessor->RegisterCuts(cutFlowManager);

  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {    
    auto event = eventReader->GetEvent(iEvent);

    cutFlowManager->UpdateCutFlow("initial");
    if(!eventProcessor->PassesTriggerCuts(event)) continue;
    cutFlowManager->UpdateCutFlow("trigger");

    if(!eventProcessor->PassesEventCuts(event, cutFlowManager)) continue;

    eventWriter->AddCurrentEvent("Events");
  }
  cutFlowManager->SaveCutFlow();
  cutFlowManager->Print();
  eventWriter->Save();

  return 0;
}
