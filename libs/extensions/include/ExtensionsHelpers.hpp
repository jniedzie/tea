#ifndef ExtensionsHelpers_hpp
#define ExtensionsHelpers_hpp

#include "Electron.hpp"
#include "GenParticle.hpp"
#include "Helpers.hpp"
#include "HepMCParticle.hpp"
#include "Jet.hpp"
#include "Muon.hpp"
#include "PhysicsObject.hpp"

inline std::shared_ptr<GenParticle> asGenParticle(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<GenParticle>(physicsObject);
}

inline std::shared_ptr<Muon> asMuon(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<Muon>(physicsObject);
}

inline std::shared_ptr<Electron> asElectron(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<Electron>(physicsObject);
}

inline std::shared_ptr<Jet> asJet(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<Jet>(physicsObject);
}

inline std::shared_ptr<HepMCParticle> asHepMCParticle(const std::shared_ptr<PhysicsObject> physicsObject, int index = -1,
                                                      int maxNdaughters = 10) {
  return std::make_shared<HepMCParticle>(physicsObject, index, maxNdaughters);
}

#endif /* ExtensionsHelpers_hpp */
