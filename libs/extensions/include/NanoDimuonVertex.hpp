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
  NanoDimuonVertex(std::shared_ptr<PhysicsObject> physicsObject_, const std::shared_ptr<Event> event);

  auto Get(std::string branchName) { return physicsObject->Get(branchName); }
  float GetAsFloat(std::string branchName) { return physicsObject->GetAsFloat(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  std::shared_ptr<PhysicsObject> Muon1() {return muon1;}
  std::shared_ptr<PhysicsObject> Muon2() {return muon2;}

  bool isDSAMuon1() { return float(physicsObject->Get("isDSAMuon1")) == 1.; }
  bool isDSAMuon2() { return float(physicsObject->Get("isDSAMuon2")) == 1.; }
  float muonIndex1() { return float(physicsObject->Get("originalMuonIdx1")); }
  float muonIndex2() { return float(physicsObject->Get("originalMuonIdx2")); }
  bool isValid() { return (float)Get("isValid") > 0; }

  std::shared_ptr<PhysicsObject> GetPhysicsObject() { return physicsObject; }

  std::string GetVertexCategory();
  std::pair<std::shared_ptr<PhysicsObject>,std::shared_ptr<PhysicsObject>> GetMuons(const std::shared_ptr<Event> event);

  TLorentzVector GetFourVector();
  float GetInvariantMass() { return GetFourVector().M(); }
  float GetPt() { return GetFourVector().Pt(); }
  float GetEta() { return GetFourVector().Eta(); }
  float GetPhi() { return GetFourVector().Phi(); }

  TVector3 GetLxyzFromPV() { return Lxyz; };
  float GetLxyFromPV() { return Lxyz.Perp(); }

  float GetCollinearityAngle();
  float GetDeltaPixelHits();

  float GetDimuonChargeProduct();

  bool PassesDCACut();
  bool PassesChi2Cut();
  bool PassesCollinearityAngleCut();
  bool PassesDeltaPixelHitsCut();
  bool PassesMaxDeltaRCut();
  bool PassesMinDeltaRCut();
  bool PassesLxyCut();
  bool PassesDimuonChargeCut();
  bool PassesVxySigmaCut();
  bool PassesHitsBeforeVertexCut();

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
  std::shared_ptr<PhysicsObject> muon1;
  std::shared_ptr<PhysicsObject> muon2;

  TVector3 Lxyz;

  std::map<std::string, float> muonVertexCuts;

  bool hasDSAMuon;
  bool hasPatMuon;

};

#endif /* NanoDimuonVertex_hpp */