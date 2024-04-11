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
  std::shared_ptr<PhysicsObjects> GetSegmentMatchedMuons(float minMatchRatio = 2.0f/3.0f);
  
  std::shared_ptr<PhysicsObjects> GetAllMuonVerticesCollection();
  std::shared_ptr<PhysicsObjects> GetVerticesForMuons(std::shared_ptr<PhysicsObjects> muonCollection);
  std::shared_ptr<PhysicsObjects> GetVertexForDimuon(std::shared_ptr<PhysicsObject> muon1, std::shared_ptr<PhysicsObject> muon2);

  bool DSAMuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index);
  bool PATMuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index);
  bool MuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index, bool isDSAMuon=false);
  float DeltaR(float eta1, float phi1, float eta2, float phi2);

  float GetMuonTriggerSF() { return muonTriggerSF; }
  void SetMuonTriggerSF(float sf) { muonTriggerSF = sf; }

  float GetNDSAMuon(std::string collectionName);
  float GetNMuon(std::string collectionName);

  std::shared_ptr<PhysicsObject> GetDSAMuonWithIndex(int muon_idx, std::string collectionName);
  std::shared_ptr<PhysicsObject> GetPATMuonWithIndex(int muon_idx, std::string collectionName);
  std::shared_ptr<PhysicsObject> GetPATorDSAMuonWithIndex(int muon_idx, std::string collectionName, bool doDSAMuons=false);
  std::pair<float,int> GetDeltaRandIndexOfClosestGenMuon(std::shared_ptr<PhysicsObject> recoMuon);

  std::shared_ptr<PhysicsObjects> GetDSAMuonsFromCollection(std::string muonCollectionName);
  std::shared_ptr<PhysicsObjects> GetPATMuonsFromCollection(std::string muonCollectionName);

 private:
  std::shared_ptr<Event> event;
  float muonTriggerSF = -1;
};

#endif /* NanoEvent_hpp */
