//  Event.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "Event.hpp"
#include "Helpers.hpp"
#include "ScaleFactorsManager.hpp"
#include "EventProcessor.hpp"

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

void Event::Reset() {
  // for (auto &[key, value] : valuesUint) value = 0;
  // for (auto &[key, value] : valuesInt) value = 0;
  // for (auto &[key, value] : valuesBool) value = 0;
  // for (auto &[key, value] : valuesFloat) value = 0;
  // for (auto &[key, value] : valuesUlong) value = 0;
  // for (auto &[key, value] : valuesUchar) value = 0;

  // for (auto &[name, collection] : collections) {
  //   for (auto element : *collection) element->Reset();
  // }

  extraCollections.clear();
}

void Event::AddExtraCollections() {
  if (!hasExtraCollections) return;

  for (auto &[name, extraCollection] : extraCollectionsDescriptions) {
    auto newCollection = make_shared<PhysicsObjects>();

    for (auto inputCollectionName : extraCollection.inputCollections) {
      auto inputCollection = GetCollection(inputCollectionName);

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

        for (auto &[branchName, flag] : extraCollection.flags) {
          bool value = physicsObject->Get(branchName);

          if (value != flag) {
            passes = false;
            break;
          }
        }

        for (auto &[branchName, option] : extraCollection.options) {
          try {
            UChar_t value = physicsObject->Get(branchName);
            if (value != option) {
              passes = false;
              break;
            }
          } catch (BadTypeException &e) {
            try {
              Int_t value = physicsObject->Get(branchName);
              if (value != option) {
                passes = false;
                break;
              }
            } catch (BadTypeException &e) {
              fatal() << e.what() << endl;
            }
          }
        }

        for (auto &[branchName, cuts] : extraCollection.optionRanges) {
          UChar_t value = physicsObject->Get(branchName);

          if (value < cuts.first || value > cuts.second) {
            passes = false;
            break;
          }
        }

        if (passes) newCollection->push_back(physicsObject);
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
  } catch (BadTypeException& e) {
    try {
      Int_t value = Get(branchName);
      defaultCollectionsTypes[branchName] = "Int_t";
      return value;
    } catch (BadTypeException& e) {
      try {
        UChar_t value = Get(branchName);
        defaultCollectionsTypes[branchName] = "UChar_t";
        return value;
      } catch (BadTypeException& e) {
        try {
          UShort_t value = Get(branchName);
          defaultCollectionsTypes[branchName] = "UShort_t";
          return value;
        } catch (BadTypeException& e) {
          try {
            Short_t value = Get(branchName);
            defaultCollectionsTypes[branchName] = "Short_t";
            return value;
          } catch (BadTypeException& e) {
            try {
              UInt_t value = Get(branchName);
              defaultCollectionsTypes[branchName] = "UInt_t";
              return value;
            } catch (BadTypeException& e) {
              try {
                Bool_t value = Get(branchName);
                defaultCollectionsTypes[branchName] = "Bool_t";
                return value;
              } catch (BadTypeException& e) {
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