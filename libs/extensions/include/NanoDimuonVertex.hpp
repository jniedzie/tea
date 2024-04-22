//  NanoDimuonVertex.hpp
//
//  Created by Lovisa Rygaard on 23/02/2024.

#ifndef NanoDimuonVertex_hpp
#define NanoDimuonVertex_hpp

#include "Event.hpp"
#include "Helpers.hpp"
#include "PhysicsObject.hpp"
#include "ScaleFactorsManager.hpp"

class NanoDimuonVertex;
typedef Collection<std::shared_ptr<NanoDimuonVertex>> NanoMuonVertices;

class NanoDimuonVertex {
 public:
  NanoDimuonVertex(std::shared_ptr<PhysicsObject> physicsObject_);

  auto Get(std::string branchName) { return physicsObject->Get(branchName); }
  float GetAsFloat(std::string branchName) { return physicsObject->GetAsFloat(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  bool isDSAMuon1() { return float(physicsObject->Get("isDSAMuon1")) == 1.; }
  bool isDSAMuon2() { return float(physicsObject->Get("isDSAMuon2")) == 1.; }
  float muonIndex1() { return float(physicsObject->Get("idx1")); }
  float muonIndex2() { return float(physicsObject->Get("idx2")); }

  std::shared_ptr<PhysicsObject> GetPhysicsObject() { return physicsObject; }

  std::string GetVertexCategory();
  std::pair<std::shared_ptr<PhysicsObject>,std::shared_ptr<PhysicsObject>> GetMuons(const std::shared_ptr<Event> event);
  float GetDimuonChargeProduct(const std::shared_ptr<Event> event);

  bool PassesChi2Cut();
  bool PassesMaxDeltaRCut();
  bool PassesMinDeltaRCut();
  bool PassesDimuonChargeCut(const std::shared_ptr<Event> event);

 private:
  std::shared_ptr<PhysicsObject> physicsObject;

  std::map<std::string, float> muonVertexCuts;

  bool hasDSAMuon;
  bool hasPatMuon;

};

#endif /* NanoDimuonVertex_hpp */