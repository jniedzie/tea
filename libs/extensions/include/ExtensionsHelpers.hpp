#ifndef ExtensionsHelpers_hpp
#define ExtensionsHelpers_hpp

#include "Helpers.hpp"
#include "HepMCParticle.hpp"
#include "NanoDimuonVertex.hpp"
#include "NanoElectron.hpp"
#include "NanoEvent.hpp"
#include "NanoGenParticle.hpp"
#include "NanoJet.hpp"
#include "NanoMuon.hpp"
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

inline std::shared_ptr<HepMCParticle> asHepMCParticle(const std::shared_ptr<PhysicsObject> physicsObject) {
  int index = physicsObject->GetIndex();
  if (index < 0) {
    fatal() << "Error in asHepMCParticle(...). Make sure to set index of the physics object using SetIndex()." << std::endl;
    exit(0);
  }
  return std::make_shared<HepMCParticle>(physicsObject, physicsObject->GetIndex());
}

inline std::shared_ptr<NanoEvent> asNanoEvent(const std::shared_ptr<Event> physicsObject) {
  return std::make_shared<NanoEvent>(physicsObject);
}

#endif /* ExtensionsHelpers_hpp */
