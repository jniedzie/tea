#ifndef NanoEvent_hpp
#define NanoEvent_hpp

#include "Event.hpp"
#include "Helpers.hpp"
#include "NanoDimuonVertex.hpp"

class NanoEvent {
 public:
  NanoEvent(std::shared_ptr<Event> event_) : event(event_) {}

  auto Get(std::string branchName) { return event->Get(branchName); }
  float GetAsFloat(std::string branchName) { return event->GetAsFloat(branchName); }
  std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const { return event->GetCollection(name); }
  void AddExtraCollections() { event->AddExtraCollections(); }

  TLorentzVector GetMetFourVector();
  float GetMetPt();

  std::shared_ptr<Event> GetEvent() { return event; }

  std::shared_ptr<PhysicsObjects> GetDRMatchedMuons(float matchingDeltaR = 0.1);
  std::shared_ptr<PhysicsObjects> GetOuterDRMatchedMuons(float matchingDeltaR = 0.1);
  std::shared_ptr<PhysicsObjects> GetSegmentMatchedMuons(float minMatchRatio = float(2/3));
  
  std::shared_ptr<PhysicsObjects> GetAllMuonVerticesCollection();
  std::shared_ptr<PhysicsObjects> GetVerticesForMuons(std::shared_ptr<PhysicsObjects> muonCollection);
  std::shared_ptr<PhysicsObjects> GetVertexForDimuon(std::shared_ptr<PhysicsObject> muon1, std::shared_ptr<PhysicsObject> muon2);

  bool MuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index, bool isDSAMuon=false);
  float DeltaR(float eta1, float phi1, float eta2, float phi2);

  float GetMuonTriggerSF() { return muonTriggerSF; }
  void SetMuonTriggerSF(float sf) { muonTriggerSF = sf; }

  float GetNDSAMuon(std::string collectionName);
  float GetNMuon(std::string collectionName);

  std::shared_ptr<PhysicsObject> GetMuonWithIndex(int muon_idx, std::string collectionName, bool isDSAMuon);

 private:
  std::shared_ptr<Event> event;
  float muonTriggerSF = -1;
};

#endif /* NanoEvent_hpp */
