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

bool HepMCParticle::FirstNonCopyMotherWithPid(int pid, const shared_ptr<PhysicsObjects> &allParticles) {
  // Loops over all particles, finding the mother of this one (i.e. such particle that one of its daughters is this one)
  // If the mother has the same PID (so it's a copy of this particle), we go to its mother (and repeat recursively). 
  // Onec we find the first mother with different PID, we check if it has the desired PID

  for(auto physicsObject : *allParticles){
    auto particle = asHepMCParticle(physicsObject);
    if (!particle) {
      error() << "Couldn't access particle..." << endl;
      continue;
    }

    if (particle->GetIndex() == index) { // skip the particle itself
      continue;
    }

    for (int daughter : particle->GetDaughters()) {
      if (daughter == index) {
        if (particle->GetPid() == GetPid()) {
          return particle->FirstNonCopyMotherWithPid(pid, allParticles);
        } else {
          return particle->GetPid() == pid;
        }
      }
    }
  }
  return false;
}

bool HepMCParticle::HasMother(int motherPid, const shared_ptr<PhysicsObjects> &allParticles) {
  info() << "mother: " << mother << " index: " << index << " pid: " << GetPid() << " motherPid: " << motherPid << endl;

  info() << "mothers: ";
  for(auto m : mothers) {
    info() << m << "\t";
  }
  info() << endl;

  if (abs(GetPid()) == motherPid) return true;
  
  if (mother == index) return false;
  if (mother == -1) return false;

  if (mother >= allParticles->size()) {
    error() << "Mother index outside of all particles range..." << endl;
  }

  auto motherParticle = asHepMCParticle(allParticles->at(mother));

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