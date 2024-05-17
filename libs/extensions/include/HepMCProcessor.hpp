#ifndef HepMCProcessor_hpp
#define HepMCProcessor_hpp

#include "ExtensionsHelpers.hpp"
#include "Helpers.hpp"
#include "HepMCParticle.hpp"
#include "PhysicsObject.hpp"

class HepMCProcessor {
 public:
  HepMCProcessor() {}

  bool IsLastCopy(std::shared_ptr<HepMCParticle> particle, const std::shared_ptr<PhysicsObjects> &allParticles) {
    for (int daughterIndex : particle->GetDaughters()) {
      if (daughterIndex < 0) continue;
      if (daughterIndex == particle->GetIndex()) return false;  // Infinite loop (particle is its own daughter)

      auto physicsObject = allParticles->at(daughterIndex);

      if(physicsObject->GetIndex() < 0) {
        fatal() << "HepMCProcessor -- IsLastCopy: some particles don't have the index set!" << std::endl;
        exit(0);
      }

      auto daughter = asHepMCParticle(physicsObject);
      if (daughter->GetPid() == particle->GetPid()) {
        return false;
      }
    }
    return true;
  }

  std::shared_ptr<HepMCParticle> GetCommonMother(std::shared_ptr<HepMCParticle> particle1, std::shared_ptr<HepMCParticle> particle2, const std::shared_ptr<PhysicsObjects> &allParticles) {
    // Get mother of particle1 and check if it's the same as mother of particle2
    auto mother1 = particle1->GetMother(allParticles);    
    if(!mother1) return nullptr;

    // loop over daughters of mother1 and check if one of them is particle2
    for (int daughterIndex : mother1->GetDaughters()) {
      if (daughterIndex < 0) continue;

      auto physicsObject = allParticles->at(daughterIndex);

      if(physicsObject->GetIndex() < 0) {
        fatal() << "HepMCProcessor -- GetCommonMother: some particles don't have the index set!" << std::endl;
        exit(0);
      }

      auto daughter = asHepMCParticle(physicsObject);
      if (daughter->GetIndex() == particle2->GetIndex()) {
        return mother1;
      }
    }
    return nullptr;
  }
};

#endif /* HepMCProcessor_hpp */
