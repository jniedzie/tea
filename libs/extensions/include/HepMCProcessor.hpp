#ifndef HepMCProcessor_hpp
#define HepMCProcessor_hpp

#include "Helpers.hpp"
#include "HepMCParticle.hpp"
#include "PhysicsObject.hpp"

class HepMCProcessor {
 public:
  HepMCProcessor() {}

  bool IsLastCopy(std::shared_ptr<HepMCParticle> particle, HepMCParticles &allParticles) {
    return particle == LastCopy(particle, allParticles);
  }

  std::shared_ptr<HepMCParticle> LastCopy(std::shared_ptr<HepMCParticle> particle, HepMCParticles &allParticles) {
    std::shared_ptr<HepMCParticle> particleCopy = particle;
    std::unordered_set<std::shared_ptr<HepMCParticle>> duplicatesCheck;
    while (NextCopy(particleCopy, allParticles)) {
      duplicatesCheck.insert(particleCopy);
      particleCopy = NextCopy(particleCopy, allParticles);
      if (duplicatesCheck.count(particleCopy)) return nullptr;
    }
    return particleCopy;
  }

  std::shared_ptr<HepMCParticle> NextCopy(std::shared_ptr<HepMCParticle> particle, HepMCParticles &allParticles) {
    for (int daughterIndex : particle->GetDaughters()) {
      if(daughterIndex < 0) continue;
      auto daughter = allParticles[daughterIndex];
      if (daughter->GetPid() == particle->GetPid()) return daughter;
    }
    return nullptr;
  }
};

#endif /* HepMCProcessor_hpp */
