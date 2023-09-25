//  Event.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "Event.hpp"

Event::Event() {}

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