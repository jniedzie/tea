//  NanoGenParticle.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "NanoGenParticle.hpp"

using namespace std;

int NanoGenParticle::GetPdgId() { return physicsObject->Get("pdgId"); }

bool NanoGenParticle::IsGoodBottomQuark(shared_ptr<NanoGenParticle> mother) {
  if (!IsFirstCopy()) return false;
  return abs(mother->GetPdgId()) == 6;  // mother must be a top
}

bool NanoGenParticle::IsGoodUdscQuark(shared_ptr<NanoGenParticle> mother) {
  if (!IsFirstCopy()) return false;
  return abs(mother->GetPdgId()) == 24;  // mother must be a W
}

bool NanoGenParticle::IsGoodLepton(shared_ptr<NanoGenParticle> mother) {
  if (!IsFirstCopy()) return false;

  // we don't want leptons from some intermediate W's
  if (!mother->IsLastCopy()) return false;

  // mother must be a W
  if (abs(mother->GetPdgId()) != 24) return false;

  return true;
}

bool NanoGenParticle::IsJet() {
  if (GetPdgId() == 21 || (abs(GetPdgId()) >= 1 && abs(GetPdgId()) <= 5)) return true;
  return false;
}

bool NanoGenParticle::IsTop() { return abs(GetPdgId()) == 6; }