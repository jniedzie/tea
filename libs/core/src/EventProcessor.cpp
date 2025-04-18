//  EventProcessor.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "EventProcessor.hpp"

using namespace std;

EventProcessor::EventProcessor() {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetVector("triggerSelection", triggerNames);
  } catch (const Exception &e) {
    warn() << "Couldn't read triggerSelection from file ";
    warn() << "(which may be fine if you're not tyring to apply trigger selection)" << endl;
  }

  try {
    config.GetCuts(eventCuts);
  } catch (const Exception &e) {
    warn() << "Couldn't read eventCuts from config file " << endl;
  }

    try {
    config.GetVector("requiredFlags", requiredFlags);
  } catch (const Exception &e) {
    warn() << "Couldn't read requiredFlags from config file " << endl;
  }

  try {
    config.GetMap("goldenJson", goldenJson);
  } catch (const Exception &e) {
    warn() << "Couldn't read goldenJson from file ";
    warn() << "(which may be fine if you're not tyring to apply golden JSON)" << endl;
  }
}

bool EventProcessor::PassesGoldenJson(const shared_ptr<Event> event) {
  bool passes = true;
  
  uint run = event->Get("run");
  uint lumi = event->Get("luminosityBlock");

  if(run == 1) return true; // MC

  if (goldenJson.find(run) == goldenJson.end()) return false;

  for (auto &lumiRange : goldenJson[run]) {
    if (lumi >= lumiRange[0] && lumi <= lumiRange[1]) {
      return true;
    }
  }
  return false;
}

bool EventProcessor::PassesTriggerCuts(const shared_ptr<Event> event) {
  bool passes = true;
  for (auto &triggerName : triggerNames) {
    passes = false;
    try {
      passes = event->Get(triggerName);
    } catch (Exception &) {
      if (find(triggerWarningsPrinted.begin(), triggerWarningsPrinted.end(), triggerName) == triggerWarningsPrinted.end()) {
        warn() << "Trigger not present: " << triggerName << endl;
        triggerWarningsPrinted.push_back(triggerName);
      }
    }
    if (passes) return true;
  }
  return passes;
}

bool EventProcessor::PassesMetFilters(const shared_ptr<Event> event){
  for(string flag : requiredFlags){
    bool flagValue = event->Get(flag);
    if(!flagValue) return false;
  }
  return true;
}

void EventProcessor::RegisterCuts(shared_ptr<CutFlowManager> cutFlowManager) {
  for (auto &[cutName, cutValues] : eventCuts) {
    cutFlowManager->RegisterCut(cutName);
  }
}

bool EventProcessor::PassesEventCuts(const shared_ptr<Event> event, shared_ptr<CutFlowManager> cutFlowManager) {
  for (auto &[cutName, cutValues] : eventCuts) {

    // TODO: this should be more generic, not only for MET_pt
    if (cutName == "MET_pt") {
      float metPt = event->Get("MET_pt");
      if (!inRange(metPt, cutValues)) return false;
    } else {
      if (!inRange(event->GetCollection(cutName.substr(1))->size(), cutValues)) return false;
    }
    if(cutFlowManager) cutFlowManager->UpdateCutFlow(cutName);
  }

  return true;
}

float EventProcessor::GetMaxPt(shared_ptr<Event> event, string collectionName) {
  auto maxPtObject = GetMaxPtObject(event, collectionName);
  if(!maxPtObject) return -1;
  float maxPt = maxPtObject->Get("pt");
  return maxPt;
}

shared_ptr<PhysicsObject> EventProcessor::GetMaxPtObject(shared_ptr<Event> event, string collectionName) {
  auto collection = event->GetCollection(collectionName);
  return GetMaxPtObject(event, collection);
}

shared_ptr<PhysicsObject> EventProcessor::GetMaxPtObject(shared_ptr<Event> event, shared_ptr<PhysicsObjects> collection) {
  float maxPt = -1;
  shared_ptr<PhysicsObject> maxPtObject = nullptr;
  for (auto element : *collection) {
    float pt = element->Get("pt");
    if (pt > maxPt) {
      maxPt = pt;
      maxPtObject = element;
    }
  }
  return maxPtObject;
}

shared_ptr<PhysicsObject> EventProcessor::GetSubleadingPtObject(shared_ptr<Event> event, string collectionName) {
  auto collection = event->GetCollection(collectionName);
  float maxPt = GetMaxPt(event, collectionName);
  float subleadingPt = -1;
  shared_ptr<PhysicsObject> subleadingPtObject = nullptr;
  for (auto element : *collection) {
    float pt = element->Get("pt");
    if (pt == maxPt) continue;
    if (pt > subleadingPt) {
      subleadingPt = pt;
      subleadingPtObject = element;
    }
  }
  return subleadingPtObject;
}

shared_ptr<PhysicsObjects> EventProcessor::GetLeadingObjects(shared_ptr<Event> event, string collectionName, size_t numObjects) {
  auto collection = event->GetCollection(collectionName);
  auto leadingObjects = make_shared<PhysicsObjects>();

  int maxNumObjects = min(numObjects, collection->size());
  for (int i = 0; i < maxNumObjects; i++) {
    auto leadingObject = GetMaxPtObject(event, collection);
    leadingObjects->push_back(leadingObject);
    auto collection_tmp = make_shared<PhysicsObjects>();
    for (auto obj : *collection) {
      if (obj == leadingObject) continue;
      collection_tmp->push_back(obj);
    }
    collection = make_shared<PhysicsObjects>(*collection_tmp);
  }
  return leadingObjects;
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
