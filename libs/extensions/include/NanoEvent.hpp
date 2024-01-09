#ifndef NanoEvent_hpp
#define NanoEvent_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class NanoEvent {
 public:
  NanoEvent(std::shared_ptr<Event> event_) : event(event_) {}

  auto Get(std::string branchName) { return event->Get(branchName); }
  float GetAsFloat(std::string branchName) { return event->GetAsFloat(branchName); }
  std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const { return event->GetCollection(name); }
  int GetCollectionSize(std::string name) { return event->GetCollectionSize(name); }
  void AddExtraCollections() { event->AddExtraCollections(); }

  TLorentzVector GetMetFourVector();
  float GetMetPt();

  std::shared_ptr<Event> GetEvent() { return event; }

  std::shared_ptr<PhysicsObjects> GetAllMuons(float matchingDeltaR = 0.1);

  float GetMuonTriggerSF() { return muonTriggerSF; }
  void SetMuonTriggerSF(float sf) { muonTriggerSF = sf; }

 private:
  std::shared_ptr<Event> event;
  float muonTriggerSF = -1;
};

#endif /* NanoEvent_hpp */
