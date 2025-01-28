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

float Event::GetAsFloat(string branchName) {
  if (defaultCollectionsTypes.count(branchName)) {
    string branchType = defaultCollectionsTypes[branchName];
    if (branchType == "Int_t") {
      Int_t value = Get(branchName);
      return value;
    }
    if (branchType == "Bool_t") {
      Bool_t value = Get(branchName);
      return value;
    }
    if (branchType == "Float_t") {
      Float_t value = Get(branchName);
      return value;
    }
    if (branchType == "UChar_t") {
      UChar_t value = Get(branchName);
      return value;
    }
    if (branchType == "UShort_t") {
      UShort_t value = Get(branchName);
      return value;
    }
    if (branchType == "Short_t") {
      Short_t value = Get(branchName);
      return value;
    }
    if (branchType == "UInt_t") {
      UInt_t value = Get(branchName);
      return value;
    }
  }

  try {
    Float_t value = Get(branchName);
    defaultCollectionsTypes[branchName] = "Float_t";
    return value;
  } catch (BadTypeException &e) {
    try {
      Int_t value = Get(branchName);
      defaultCollectionsTypes[branchName] = "Int_t";
      return value;
    } catch (BadTypeException &e) {
      try {
        UChar_t value = Get(branchName);
        defaultCollectionsTypes[branchName] = "UChar_t";
        return value;
      } catch (BadTypeException &e) {
        try {
          UShort_t value = Get(branchName);
          defaultCollectionsTypes[branchName] = "UShort_t";
          return value;
        } catch (BadTypeException &e) {
          try {
            Short_t value = Get(branchName);
            defaultCollectionsTypes[branchName] = "Short_t";
            return value;
          } catch (BadTypeException &e) {
            try {
              UInt_t value = Get(branchName);
              defaultCollectionsTypes[branchName] = "UInt_t";
              return value;
            } catch (BadTypeException &e) {
              try {
                Bool_t value = Get(branchName);
                defaultCollectionsTypes[branchName] = "Bool_t";
                return value;
              } catch (BadTypeException &e) {
                error() << "Couldn't get value for branch " << branchName << endl;
              }
            }
          }
        }
      }
    }
  }
  return 0;
}