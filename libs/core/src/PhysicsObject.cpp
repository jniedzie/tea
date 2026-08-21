//  PhysicsObject.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "PhysicsObject.hpp"

#include <algorithm>

using namespace std;

namespace {
// Objects that had a custom value set since the last Event::Reset(). Keeping the list means clearing
// is proportional to the number of objects the app actually touched, rather than to all
// maxCollectionElements objects of every collection.
vector<PhysicsObject *> objectsWithCustomValues;
}  // namespace

PhysicsObject::PhysicsObject(std::string originalCollection_, int index_)
    : originalCollection(originalCollection_), index(index_) {}

void PhysicsObject::RememberCustomValues() {
  if (hasCustomValues) return;
  hasCustomValues = true;
  objectsWithCustomValues.push_back(this);
}

void PhysicsObject::ForgetCustomValues() {
  if (!hasCustomValues) return;
  hasCustomValues = false;
  objectsWithCustomValues.erase(remove(objectsWithCustomValues.begin(), objectsWithCustomValues.end(), this),
                                objectsWithCustomValues.end());
}

void PhysicsObject::ClearAllCustomValues() {
  for (auto *physicsObject : objectsWithCustomValues) {
    physicsObject->customValuesTypes.clear();
    physicsObject->hasCustomValues = false;
  }
  objectsWithCustomValues.clear();
}

void PhysicsObject::Reset() {
  for (auto &[key, value] : valuesUint)
    value = 0;
  for (auto &[key, value] : valuesInt)
    value = 0;
  for (auto &[key, value] : valuesBool)
    value = 0;
  for (auto &[key, value] : valuesFloat)
    value = 0;
  for (auto &[key, value] : customValuesFloat)
    value = 0;
  for (auto &[key, value] : valuesUlong)
    value = 0;
  for (auto &[key, value] : valuesUchar)
    value = 0;
  for (auto &[key, value] : valuesChar)
    value = 0;
}
