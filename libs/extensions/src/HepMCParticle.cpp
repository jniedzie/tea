#include "HepMCParticle.hpp"

#include "HepMCProcessor.hpp"

using namespace std;

HepMCParticle::HepMCParticle(shared_ptr<PhysicsObject> physicsObject_, int index_)
    : physicsObject(physicsObject_), index(index_) {
  
  for (int i = 0; i < maxNdaughters; i++) daughters.emplace_back(-1);
  SetupDaughters();
}

void HepMCParticle::SetupDaughters() {
  for (int i = 0; i < maxNdaughters; i++) {
    daughters[i] = physicsObject->Get("d" + to_string(i));
  }
}

shared_ptr<HepMCParticle> HepMCParticle::GetMother(const shared_ptr<PhysicsObjects> &allParticles) {
  // Returns the first mother of the particle that's not its own copy

  for (int particleIndex = 0; particleIndex < allParticles->size(); particleIndex++) {
    auto physicsObject = allParticles->at(particleIndex);
    auto particle = asHepMCParticle(physicsObject);
    if (!particle) {
      error() << "Couldn't access particle..." << endl;
      continue;
    }

    if (particle->GetIndex() == index) {  // skip the particle itself
      continue;
    }

    for (int daughter : particle->GetDaughters()) {
      if (daughter != index) continue;
      return (particle->GetPid() == GetPid()) ? particle->GetMother(allParticles) : particle;
    }
  }
  return nullptr;
}
