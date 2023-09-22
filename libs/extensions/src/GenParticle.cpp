//  GenParticle.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "GenParticle.hpp"

using namespace std;

int GenParticle::GetPdgId() { return physicsObject->Get("pdgId"); }

bool GenParticle::IsGoodBottomQuark(shared_ptr<GenParticle> mother) {
  if (!IsFirstCopy()) return false;
  return abs(mother->GetPdgId()) == 6;  // mother must be a top
}

bool GenParticle::IsGoodUdscQuark(shared_ptr<GenParticle> mother) {
  if (!IsFirstCopy()) return false;
  return abs(mother->GetPdgId()) == 24;  // mother must be a W
}

bool GenParticle::IsGoodLepton(shared_ptr<GenParticle> mother) {
  if (!IsFirstCopy()) return false;

  // we don't want leptons from some intermediate W's
  if (!mother->IsLastCopy()) return false;

  // mother must be a W
  if (abs(mother->GetPdgId()) != 24) return false;

  return true;
}

bool GenParticle::IsJet() {
  if (GetPdgId() == 21 || (abs(GetPdgId()) >= 1 && abs(GetPdgId()) <= 5)) return true;
  return false;
}

bool GenParticle::IsTop() { return abs(GetPdgId()) == 6; }