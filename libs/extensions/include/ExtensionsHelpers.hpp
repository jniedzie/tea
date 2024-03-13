#ifndef ExtensionsHelpers_hpp
#define ExtensionsHelpers_hpp

#include "NanoElectron.hpp"
#include "NanoGenParticle.hpp"
#include "Helpers.hpp"
#include "HepMCParticle.hpp"
#include "NanoJet.hpp"
#include "NanoMuon.hpp"
#include "NanoDimuonVertex.hpp"
#include "NanoEvent.hpp"
#include "PhysicsObject.hpp"

inline std::shared_ptr<NanoGenParticle> asNanoGenParticle(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<NanoGenParticle>(physicsObject);
}

inline std::shared_ptr<NanoMuon> asNanoMuon(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<NanoMuon>(physicsObject);
}

inline std::shared_ptr<NanoDimuonVertex> asNanoDimuonVertex(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<NanoDimuonVertex>(physicsObject);
}

inline std::shared_ptr<NanoElectron> asNanoElectron(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<NanoElectron>(physicsObject);
}

inline std::shared_ptr<NanoJet> asNanoJet(const std::shared_ptr<PhysicsObject> physicsObject) {
  return std::make_shared<NanoJet>(physicsObject);
}

inline std::shared_ptr<HepMCParticle> asHepMCParticle(const std::shared_ptr<PhysicsObject> physicsObject, int index = -1,
                                                      int maxNdaughters = 10) {
  return std::make_shared<HepMCParticle>(physicsObject, index, maxNdaughters);
}

inline std::shared_ptr<NanoEvent> asNanoEvent(const std::shared_ptr<Event> physicsObject) {
  return std::make_shared<NanoEvent>(physicsObject);
}

#endif /* ExtensionsHelpers_hpp */
