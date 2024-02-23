//  NanoGenParticle.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "NanoGenParticle.hpp"

using namespace std;

float NanoGenParticle::GetDxy(float pv_x, float pv_y) {
  float vx = physicsObject->Get("vx");
  float vy = physicsObject->Get("vy");
  float phi = physicsObject->Get("phi");

  float dxy = -(vx-pv_x)*sin(phi) + (vy-pv_y)*cos(phi);
  return dxy;
}

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

bool NanoGenParticle::IsGoodParticleWithID(int pdgId) {
  if (!IsFirstCopy()) return false;
  if(abs(GetPdgId()) != pdgId) return false;

  return true;
}

bool NanoGenParticle::IsJet() {
  if (GetPdgId() == 21 || (abs(GetPdgId()) >= 1 && abs(GetPdgId()) <= 5)) return true;
  return false;
}

bool NanoGenParticle::IsTop() { return abs(GetPdgId()) == 6; }

bool NanoGenParticle::IsMuon() { return abs(GetPdgId()) == 13; }
