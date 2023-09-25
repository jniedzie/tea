#include "HepMCParticle.hpp"

#include "HepMCProcessor.hpp"
#include "Profiler.hpp"

using namespace std;

HepMCParticle::HepMCParticle(shared_ptr<PhysicsObject> physicsObject_, int index_, int maxNdaughters_)
    : physicsObject(physicsObject_), maxNdaughters(maxNdaughters_), index(index_), mother(-1) {
  if (maxNdaughters > 100) maxNdaughters = 100;

  for (int i = 0; i < maxNdaughters; i++) daughters.push_back(-1);
  SetupDaughters();
}

void HepMCParticle::SetupDaughters() {
  for (int i = 0; i < maxNdaughters; i++) {
    daughters[i] = physicsObject->Get("d" + to_string(i));
  }
}

bool HepMCParticle::HasMother(int motherPid, const HepMCParticles &allParticles) {
  if (abs(GetPid()) == motherPid) return true;
  if (mother == index) return false;
  if (mother == -1) return false;

  if (mother >= allParticles.size()) {
    error() << "Mother index outside of all particles range..." << endl;
  }

  auto motherParticle = allParticles.at(mother);

  if (!motherParticle) {
    error() << "Couldn't access mother particle..." << endl;
  }
  if (motherParticle->HasMother(motherPid, allParticles)) return true;

  return false;
}

bool HepMCParticle::IsMother(int motherPid, const HepMCParticles &allParticles) {
  if (abs(GetPid()) == motherPid) return true;

  int originalPid = GetPid();

  bool containsNonIdenticalMother = false;
  bool isMotherGoodPid = false;

  for (int m : mothers) {
    if (m == -1) continue;

    auto motherParticle = allParticles[m];

    if (motherParticle->GetIndex() == index) {
      continue;
    }
    if (motherParticle->GetPid() != originalPid) {
      containsNonIdenticalMother = true;
      isMotherGoodPid |= motherParticle->GetPid() == motherPid;
    }
  }

  if (containsNonIdenticalMother) {
    return isMotherGoodPid;
  }

  bool anyOfMothersGood = false;
  for (int m : mothers) {
    if (m == -1) continue;
    auto motherParticle = allParticles[m];
    anyOfMothersGood |= motherParticle->IsMother(motherPid, allParticles);
  }

  return anyOfMothersGood;
}