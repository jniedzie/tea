//  EventProcessor.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "EventProcessor.hpp"

#include "ExtensionsHelpers.hpp"

using namespace std;

EventProcessor::EventProcessor(string configPath) {
  if (configPath != "") {
    config = std::make_unique<ConfigManager>(configPath);
    try {
      config->GetVector("triggerSelection", triggerNames);
    }
    catch (const Exception& e){
      warn() << "Couldn't read triggerSelection from config file ";
      warn() << "(which may be fine if you're not tyring to apply trigger selectinon)\n";
    }

    try {
      config->GetSelections(eventSelections);
    }
    catch (const Exception& e){
      warn() << "Couldn't read eventSelections from config file ";
    }
  }
}

float EventProcessor::GetMaxPt(shared_ptr<Event> event, string collectionName) {
  auto collection = event->GetCollection(collectionName);

  float maxPt = 0;
  for (auto element : *collection) {
    float pt = element->Get("pt");
    if (pt > maxPt) maxPt = pt;
  }
  return maxPt;
}

float EventProcessor::GetHt(shared_ptr<Event> event, string collectionName) {
  auto collection = event->GetCollection(collectionName);
  float ht = 0;
  for (auto element : *collection) {
    float pt = element->Get("pt");
    ht += pt;
  }
  return ht;
}

void EventProcessor::AddExtraCollections(shared_ptr<Event> event) {
  map<string, ExtraCollection> extraEventCollections;
  config->GetExtraEventCollections(extraEventCollections);

  for (auto &[name, extraCollection] : extraEventCollections) {
    auto newCollection = make_shared<PhysicsObjects>();

    for (auto inputCollectionName : extraCollection.inputCollections) {
      auto inputCollection = event->GetCollection(inputCollectionName);

      int n = 0;
      for (auto physicsObject : *inputCollection) {
        n++;

        bool passes = true;

        for (auto &[branchName, cuts] : extraCollection.selections) {
          float value = physicsObject->Get(branchName);

          if (value < cuts.first || value > cuts.second) {
            passes = false;
            break;
          }
        }

        if (passes) newCollection->push_back(physicsObject);
      }
    }
    event->AddExtraCollection(name, newCollection);
  }
}
