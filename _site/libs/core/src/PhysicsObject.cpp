//  PhysicsObject.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "PhysicsObject.hpp"

PhysicsObject::PhysicsObject(std::string originalCollection_) : originalCollection(originalCollection_) {}

void PhysicsObject::Reset() {
  for (auto &[key, value] : valuesUint) value = 0;
  for (auto &[key, value] : valuesInt) value = 0;
  for (auto &[key, value] : valuesBool) value = 0;
  for (auto &[key, value] : valuesFloat) value = 0;
  for (auto &[key, value] : valuesUlong) value = 0;
  for (auto &[key, value] : valuesUchar) value = 0;
}