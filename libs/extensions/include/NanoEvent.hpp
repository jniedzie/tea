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

  std::shared_ptr<NanoMuons> GetDRMatchedMuons(std::shared_ptr<NanoMuons> muonCollection, float matchingDeltaR = 0.1);
  std::shared_ptr<NanoMuons> GetOuterDRMatchedMuons(std::shared_ptr<NanoMuons> muonCollection, float matchingDeltaR = 0.1);
  std::shared_ptr<NanoMuons> GetProximityDRMatchedMuons(std::shared_ptr<NanoMuons> muonCollection, float matchingDeltaR = 0.1);
  std::shared_ptr<NanoMuons> GetSegmentMatchedMuons(std::shared_ptr<NanoMuons> muonCollection, float minMatchRatio = 2.0f / 3.0f);
  std::shared_ptr<NanoDimuonVertex> GetSegmentMatchedBestDimuonVertex(std::shared_ptr<NanoDimuonVertex> bestVertex, std::shared_ptr<NanoDimuonVertices> goodVerticesCollection, float minMatchRatio = 2.0f / 3.0f);

  std::shared_ptr<PhysicsObjects> GetAllMuonVerticesCollection();
  std::shared_ptr<PhysicsObjects> GetVerticesForMuons(std::shared_ptr<NanoMuons> muonCollection);
  std::shared_ptr<PhysicsObject> GetVertexForDimuon(std::shared_ptr<NanoMuon> muon1, std::shared_ptr<NanoMuon> muon2);
  std::shared_ptr<PhysicsObjects> GetVerticesForDimuons(std::shared_ptr<NanoMuonPairs> dimuons);

  bool DSAMuonIndexExist(std::shared_ptr<NanoMuons> muons, float index);
  bool PATMuonIndexExist(std::shared_ptr<NanoMuons> muons, float index);
  bool MuonIndexExist(std::shared_ptr<NanoMuons> muons, float index, bool isDSAMuon = false);
  float DeltaR(float eta1, float phi1, float eta2, float phi2);

  std::map<std::string, float> GetMuonTriggerScaleFactors() { return muonTriggerSF; }
  void SetMuonTriggerScaleFactors(std::map<std::string, float> sf) { muonTriggerSF = sf; }

  float GetNDSAMuon(std::string collectionName);
  float GetNMuon(std::string collectionName);

  std::shared_ptr<NanoMuon> GetDSAMuonWithIndex(int muon_idx, std::string collectionName);
  std::shared_ptr<NanoMuon> GetPATMuonWithIndex(int muon_idx, std::string collectionName);
  std::shared_ptr<NanoMuon> GetPATorDSAMuonWithIndex(int muon_idx, std::string collectionName, bool doDSAMuons = false);
  std::pair<float, int> GetDeltaRandIndexOfClosestGenMuon(std::shared_ptr<NanoMuon> recoMuon);

  std::shared_ptr<NanoMuons> GetDSAMuonsFromCollection(std::string muonCollectionName);
  std::shared_ptr<NanoMuons> GetDSAMuonsFromCollection(std::shared_ptr<NanoMuons> muonCollection);
  std::shared_ptr<NanoMuons> GetPATMuonsFromCollection(std::string muonCollectionName);
  std::shared_ptr<NanoMuons> GetPATMuonsFromCollection(std::shared_ptr<NanoMuons> muonCollection);

  std::shared_ptr<NanoMuons> GetAllCommonMuonsInCollections(std::shared_ptr<NanoMuons> muonCollection1, std::shared_ptr<NanoMuons> muonCollection2);

 private:
  std::shared_ptr<Event> event;
  std::map<std::string, float> muonTriggerSF;
};

#endif /* NanoEvent_hpp */
