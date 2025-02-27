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
  for (auto& [key, value] : valuesChar) value = 0;
}
