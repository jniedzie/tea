//  PhysicsObject.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "PhysicsObject.hpp"

using namespace std;

PhysicsObject::PhysicsObject(std::string originalCollection_, int index_) : originalCollection(originalCollection_), index(index_) {}

void PhysicsObject::Reset() {
  for (auto& [key, value] : valuesUint) value = 0;
  for (auto& [key, value] : valuesInt) value = 0;
  for (auto& [key, value] : valuesBool) value = 0;
  for (auto& [key, value] : valuesFloat) value = 0;
  for (auto& [key, value] : valuesUlong) value = 0;
  for (auto& [key, value] : valuesUchar) value = 0;
}

float PhysicsObject::GetAsFloat(string branchName) {
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