//  Event.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "Event.hpp"

#include "EventProcessor.hpp"
#include "Helpers.hpp"
#include "ScaleFactorsManager.hpp"

using namespace std;

#include "Helpers.hpp"

using namespace std;

Event::Event() {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetExtraEventCollections(extraCollectionsDescriptions);
  } catch (const Exception &e) {
    info() << "No extra event collections found" << endl;
    hasExtraCollections = false;
  }
}

Event::~Event() {}

void Event::Reset() { extraCollections.clear(); }

template <typename First, typename... Rest>
bool Event::tryGet(shared_ptr<PhysicsObject> physicsObject, string branchName, pair<float, float> cuts) {
  try {
    First value = physicsObject->Get(branchName);
    return value >= cuts.first && value <= cuts.second;
  } catch (BadTypeException &e) {
    if constexpr (sizeof...(Rest) > 0) {
      return tryGet<Rest...>(physicsObject, branchName, cuts);
    } else {
      fatal() << e.what() << endl;
      gErrorIgnoreLevel = kFatal;
      exit(0);
    }
  }
}

bool Event::checkCuts(shared_ptr<PhysicsObject> physicsObject, string branchName, pair<float, float> cuts) {
  // important: checking float first makes things much faster, since most branches are floats
  return tryGet<Float_t, Bool_t, UChar_t, UInt_t, Int_t, Short_t>(physicsObject, branchName, cuts);
}

void Event::AddExtraCollections() {
  if (!hasExtraCollections) return;

  for (auto &[name, extraCollection] : extraCollectionsDescriptions) {
    auto newCollection = make_shared<PhysicsObjects>();

    for (auto inputCollectionName : extraCollection.inputCollections) {
      
      shared_ptr<PhysicsObjects> inputCollection; 
      
      try{
        inputCollection = GetCollection(inputCollectionName);
      }
      catch(Exception &e){
        error() << "Couldn't find collection " << inputCollectionName << " for extra collection " << name << endl;
        continue;
      }

      for (auto physicsObject : *inputCollection) {
        bool passes = true;

        for (auto &[branchName, flag] : extraCollection.flags) {
          passes = checkCuts(physicsObject, branchName, {flag, flag});
          if (!passes) break;
        }
        if (!passes) continue;

        for (auto &[branchName, cuts] : extraCollection.allCuts) {
          passes = checkCuts(physicsObject, branchName, cuts);
          if (!passes) break;
        }
        if (!passes) continue;

        newCollection->push_back(physicsObject);
      }
    }
    extraCollections.insert({name, newCollection});
  }
}
