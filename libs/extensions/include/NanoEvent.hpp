#ifndef NanoEvent_hpp
#define NanoEvent_hpp

#include "Event.hpp"
#include "Helpers.hpp"
#include "NanoDimuonVertex.hpp"

typedef std::pair<std::shared_ptr<PhysicsObject>, std::shared_ptr<PhysicsObject>> MuonPair;
typedef Collection<MuonPair> MuonPairs;

class NanoEvent {
 public:
  NanoEvent(std::shared_ptr<Event> event_) : event(event_) {}

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return event->Get(branchName, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return event->GetAs<T>(branchName); }
  std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const { return event->GetCollection(name); }
  void AddExtraCollections() { event->AddExtraCollections(); }

  TLorentzVector GetMetFourVector();
  float GetMetPt();

  std::shared_ptr<Event> GetEvent() { return event; }

  std::shared_ptr<PhysicsObjects> GetDRMatchedMuons(std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection,
                                                    float matchingDeltaR = 0.1);
  std::shared_ptr<PhysicsObjects> GetOuterDRMatchedMuons(
      std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection, float matchingDeltaR = 0.1);
  std::shared_ptr<PhysicsObjects> GetProximityDRMatchedMuons(
      std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection, float matchingDeltaR = 0.1);
  std::shared_ptr<PhysicsObjects> GetSegmentMatchedMuons(
      std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection, float minMatchRatio = 2.0f / 3.0f);

  std::shared_ptr<PhysicsObjects> GetAllMuonVerticesCollection();
  std::shared_ptr<PhysicsObjects> GetVerticesForMuons(std::shared_ptr<PhysicsObjects> muonCollection);
  std::shared_ptr<PhysicsObject> GetVertexForDimuon(std::shared_ptr<PhysicsObject> muon1, std::shared_ptr<PhysicsObject> muon2);
  std::shared_ptr<PhysicsObjects> GetVerticesForDimuons(std::shared_ptr<MuonPairs> dimuons);

  bool DSAMuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index);
  bool PATMuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index);
  bool MuonIndexExist(std::shared_ptr<PhysicsObjects> objectCollection, float index, bool isDSAMuon = false);
  float DeltaR(float eta1, float phi1, float eta2, float phi2);

  float GetMuonTriggerSF() { return muonTriggerSF; }
  void SetMuonTriggerSF(float sf) { muonTriggerSF = sf; }

  float GetNDSAMuon(std::string collectionName);
  float GetNMuon(std::string collectionName);

  std::shared_ptr<PhysicsObject> GetDSAMuonWithIndex(int muon_idx, std::string collectionName);
  std::shared_ptr<PhysicsObject> GetPATMuonWithIndex(int muon_idx, std::string collectionName);
  std::shared_ptr<PhysicsObject> GetPATorDSAMuonWithIndex(int muon_idx, std::string collectionName, bool doDSAMuons = false);
  std::pair<float, int> GetDeltaRandIndexOfClosestGenMuon(std::shared_ptr<PhysicsObject> recoMuon);

  std::shared_ptr<PhysicsObjects> GetDSAMuonsFromCollection(std::string muonCollectionName);
  std::shared_ptr<PhysicsObjects> GetDSAMuonsFromCollection(std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection);
  std::shared_ptr<PhysicsObjects> GetPATMuonsFromCollection(std::string muonCollectionName);
  std::shared_ptr<PhysicsObjects> GetPATMuonsFromCollection(std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection);

  std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> GetAllCommonMuonsInCollections(
      std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection1,
      std::shared_ptr<Collection<std::shared_ptr<PhysicsObject>>> muonCollection2);

 private:
  std::shared_ptr<Event> event;
  float muonTriggerSF = -1;
};

#endif /* NanoEvent_hpp */
