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

    // Demonstrate branchesToAdd: dimuonMass is app-set only (config varexp "-1.0" is just the
    // fallback default). Muon_ptSquared is config-computed via varexp "Muon_pt**2"; overriding
    // it here for muon 0 only demonstrates that an app Set<T> call wins over the varexp.
    auto muons = event->GetCollection("Muon");
    if (muons->size() >= 2) {
      auto p1 = muons->at(0)->GetFourVector();
      auto p2 = muons->at(1)->GetFourVector();
      event->Set<float>("dimuonMass", static_cast<float>((p1 + p2).M()));
    }
    if (!muons->empty()) {
      float pt = muons->at(0)->GetAs<float>("pt");
      muons->at(0)->Set<float>("ptSquared", pt * pt + 1.f);
    }

    // Demonstrate a free-standing vector branch: not tied to any collection's size branch,
    // so it's set unconditionally (even when empty) rather than skipped like the scalars above.
    vector<float> muonPts;
    for (auto &muon : *muons) muonPts.push_back(muon->GetAs<float>("pt"));
    event->SetVector<float>("muonPt", muonPts);

    eventWriter->AddCurrentEvent("Events");
  }
  cutFlowManager->SaveCutFlow();
  cutFlowManager->Print();
  eventWriter->Save();

  return 0;
}
