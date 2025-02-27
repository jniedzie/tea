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

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return physicsObject->GetAs<T>(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  std::shared_ptr<PhysicsObject> Muon1() { return muon1; }
  std::shared_ptr<PhysicsObject> Muon2() { return muon2; }

  bool isDSAMuon1() { return float(physicsObject->Get("isDSAMuon1")) == 1.; }
  bool isDSAMuon2() { return float(physicsObject->Get("isDSAMuon2")) == 1.; }
  float muonIndex1() { return float(physicsObject->Get("originalMuonIdx1")); }
  float muonIndex2() { return float(physicsObject->Get("originalMuonIdx2")); }
  bool isValid() { return (float)Get("isValid") > 0; }

  std::shared_ptr<PhysicsObject> GetPhysicsObject() { return physicsObject; }

  std::string GetVertexCategory();
  std::pair<std::shared_ptr<PhysicsObject>, std::shared_ptr<PhysicsObject>> GetMuons(const std::shared_ptr<Event> event);

  TLorentzVector GetFourVector();
  float GetInvariantMass() { return GetFourVector().M(); }
  float GetDimuonPt() { return GetFourVector().Pt(); }
  float GetDimuonEta() { return GetFourVector().Eta(); }
  float GetDimuonPhi() { return GetFourVector().Phi(); }

  TVector3 GetLxyzFromPV() { return Lxyz; };
  float GetLxyFromPV() { return Lxyz.Perp(); }
  float GetLxySigmaFromPV() { return LxySigma; }

  float GetCollinearityAngle();
  float GetDPhiBetweenMuonpTAndLxy(int muonIndex);
  float GetDPhiBetweenDimuonpTAndPtMiss(TLorentzVector ptMissFourVector);
  float GetDeltaPixelHits();
  float Get3DOpeningAngle();
  float GetCosine3DOpeningAngle();

  float GetDimuonChargeProduct();
  float GetOuterDeltaR();

  float GetDeltaEta();
  float GetDeltaPhi();
  float GetOuterDeltaEta();
  float GetOuterDeltaPhi();

  int GetTotalNumberOfSegments();
  int GetTotalNumberOfDTHits();
  int GetTotalNumberOfCSCHits();

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
  std::shared_ptr<PhysicsObject> muon1;
  std::shared_ptr<PhysicsObject> muon2;

  TVector3 Lxyz;
  float LxySigma;

  bool hasDSAMuon;
  bool hasPatMuon;
};

#endif /* NanoDimuonVertex_hpp */