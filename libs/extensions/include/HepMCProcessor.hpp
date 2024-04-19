#ifndef HepMCProcessor_hpp
#define HepMCProcessor_hpp

#include "ExtensionsHelpers.hpp"
#include "Helpers.hpp"
#include "HepMCParticle.hpp"
#include "PhysicsObject.hpp"

class HepMCProcessor {
 public:
  HepMCProcessor() {}

  bool IsLastCopy(std::shared_ptr<HepMCParticle> particle, int particleIndex, const std::shared_ptr<PhysicsObjects> &allParticles) {
    for (int daughterIndex : particle->GetDaughters()) {
      if (daughterIndex < 0) continue;
      if (daughterIndex == particleIndex) return false;  // Infinite loop (particle is its own daughter)

      auto daughter = asHepMCParticle(allParticles->at(daughterIndex));
      if (daughter->GetPid() == particle->GetPid()) {
        return false;
      }
    }
    return true;
  }
};

#endif /* HepMCProcessor_hpp */
