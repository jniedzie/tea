//  NanoGenParticle.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "NanoGenParticle.hpp"

using namespace std;

TLorentzVector NanoGenParticle::GetFourVector(float mass) {
    TLorentzVector v;
    v.SetPtEtaPhiM(physicsObject->Get("pt"), physicsObject->Get("eta"), physicsObject->Get("phi"), mass);
    return v;
  }

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

shared_ptr<NanoGenParticle> NanoGenParticle::GetFirstCopy(shared_ptr<PhysicsObjects> genParticles) {
  int motherIndex = GetMotherIndex();
  if (motherIndex < 0) return nullptr;
  auto mother = make_shared<NanoGenParticle>(genParticles->at(motherIndex));
  int pdgId = abs(GetPdgId());
  
  shared_ptr<NanoGenParticle> firstCopy = make_shared<NanoGenParticle>(*this);

  while(abs(mother->GetPdgId()) == pdgId) {
    firstCopy = mother;
    motherIndex = mother->GetMotherIndex();
    if (motherIndex < 0) return nullptr;
    mother = make_shared<NanoGenParticle>(genParticles->at(motherIndex));
  }
  return firstCopy;
}
