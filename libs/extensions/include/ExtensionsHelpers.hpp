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

inline std::shared_ptr<PhysicsObjects> asPhysicsObjects(const std::shared_ptr<NanoMuons> muons){
  if(!muons) return nullptr;
  auto physicsObjects = std::make_shared<PhysicsObjects>();
  for(auto muon : *muons) {
    physicsObjects->push_back(muon->GetPhysicsObject());
  }
  return physicsObjects;
}

inline std::shared_ptr<NanoGenParticle> asNanoGenParticle(const std::shared_ptr<PhysicsObject> physicsObject) {
  if(!physicsObject) return nullptr;
  return std::make_shared<NanoGenParticle>(physicsObject);
}

inline std::shared_ptr<NanoMuon> asNanoMuon(const std::shared_ptr<PhysicsObject> physicsObject) {
  if(!physicsObject) return nullptr;
  return std::make_shared<NanoMuon>(physicsObject);
}

inline std::shared_ptr<NanoMuons> asNanoMuons(const std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> physicsObjects) {
  if(!physicsObjects) return nullptr;
  auto nanoMuons = std::make_shared<NanoMuons>();
  for(auto physicsObject : *physicsObjects) {
    nanoMuons->push_back(asNanoMuon(physicsObject));
  }
  return nanoMuons;
}

inline std::shared_ptr<NanoDimuonVertex> asNanoDimuonVertex(const std::shared_ptr<PhysicsObject> physicsObject, const std::shared_ptr<Event> event) {
  if(!physicsObject || !event) return nullptr;
  return std::make_shared<NanoDimuonVertex>(physicsObject, event);
}

inline std::shared_ptr<NanoDimuonVertices> asNanoDimuonVertices(const std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> physicsObjects, const std::shared_ptr<Event> event) {
  if(!physicsObjects || !event) return nullptr;
  auto nanoDimuonVertices = std::make_shared<NanoDimuonVertices>();
  for(auto physicsObject : *physicsObjects) {
    nanoDimuonVertices->push_back(asNanoDimuonVertex(physicsObject,event));
  }
  return nanoDimuonVertices;
}

inline std::shared_ptr<NanoElectron> asNanoElectron(const std::shared_ptr<PhysicsObject> physicsObject) {
  if(!physicsObject) return nullptr;
  return std::make_shared<NanoElectron>(physicsObject);
}

inline std::shared_ptr<NanoJet> asNanoJet(const std::shared_ptr<PhysicsObject> physicsObject) {
  if(!physicsObject) return nullptr;
  return std::make_shared<NanoJet>(physicsObject);
}

inline std::shared_ptr<NanoJets> asNanoJets(const std::shared_ptr<PhysicsObjects> physicsObjects) {
  if(!physicsObjects) return nullptr;
  auto nanoJets = std::make_shared<NanoJets>();
  for(auto physicsObject : *physicsObjects) {
    nanoJets->push_back(asNanoJet(physicsObject));
  }
  return nanoJets;
}

inline std::shared_ptr<HepMCParticle> asHepMCParticle(const std::shared_ptr<PhysicsObject> physicsObject) {
  if(!physicsObject) return nullptr;
  
  int index = physicsObject->GetIndex();
  if (index < 0) {
    fatal() << "Error in asHepMCParticle(...). Make sure to set index of the physics object using SetIndex()." << std::endl;
    exit(1);
  }
  return std::make_shared<HepMCParticle>(physicsObject, physicsObject->GetIndex());
}

inline std::shared_ptr<NanoEvent> asNanoEvent(const std::shared_ptr<Event> physicsObject) {
  if(!physicsObject) return nullptr;
  return std::make_shared<NanoEvent>(physicsObject);
}

#endif /* ExtensionsHelpers_hpp */
