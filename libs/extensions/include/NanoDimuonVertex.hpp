//  NanoDimuonVertex.hpp
//
//  Created by Lovisa Rygaard on 23/02/2024.

#ifndef NanoDimuonVertex_hpp
#define NanoDimuonVertex_hpp

#include "Event.hpp"
#include "Helpers.hpp"
#include "PhysicsObject.hpp"
#include "ScaleFactorsManager.hpp"
#include "NanoMuon.hpp"

class NanoDimuonVertex;
typedef Collection<std::shared_ptr<NanoDimuonVertex>> NanoDimuonVertices;

class NanoDimuonVertex {
 public:
  NanoDimuonVertex(std::shared_ptr<PhysicsObject> physicsObject_, const std::shared_ptr<Event> event);

  auto Get(std::string branchName, bool verbose = true, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, verbose, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return physicsObject->GetAs<T>(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  std::shared_ptr<NanoMuon> Muon1() { return muon1; }
  std::shared_ptr<NanoMuon> Muon2() { return muon2; }

  bool IsDSAMuon1() { return float(physicsObject->Get("isDSAMuon1")) == 1.; }
  bool IsDSAMuon2() { return float(physicsObject->Get("isDSAMuon2")) == 1.; }
  float MuonIndex1() { return float(physicsObject->Get("originalMuonIdx1")); }
  float MuonIndex2() { return float(physicsObject->Get("originalMuonIdx2")); }
  bool IsValid() { return (float)Get("isValid") > 0; }

  bool IsPatDimuon() { return GetVertexCategory() == "Pat"; }
  bool IsPatDSADimuon() { return GetVertexCategory() == "PatDSA"; }
  bool IsDSADimuon() { return GetVertexCategory() == "DSA"; }

  std::shared_ptr<PhysicsObject> GetPhysicsObject() { return physicsObject; }

  std::string GetVertexCategory();
  std::pair<std::shared_ptr<NanoMuon>, std::shared_ptr<NanoMuon>> GetMuons(const std::shared_ptr<Event> event);

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
  float GetDeltaR() { return Get("dR"); }

  float GetDeltaEta();
  float GetDeltaPhi();
  float GetOuterDeltaEta();
  float GetOuterDeltaPhi();
  float GetLeadingMuonPt();

  float GetLogDisplacedTrackIso(std::string isolationVariable);
  float GetDeltaDisplacedTrackIso03();
  float GetLogDeltaDisplacedTrackIso03();
  float GetDeltaDisplacedTrackIso04();
  float GetLogDeltaDisplacedTrackIso04();
  float GetLogDeltaSquaredDisplacedTrackIso03();
  float GetLogDeltaSquaredDisplacedTrackIso04();

  int GetTotalNumberOfSegments();
  int GetTotalNumberOfDTHits();
  int GetTotalNumberOfCSCHits();

  std::shared_ptr<NanoMuon> GetLeadingMuon();
  std::shared_ptr<NanoMuon> GetSubleadingMuon();

  bool HasMuonIndices(int muonIdx1, int muonIdx2);

  std::string GetGenMotherCategory(std::shared_ptr<PhysicsObjects> genMuonCollection);
  std::shared_ptr<PhysicsObjects> GetGenMothers(std::shared_ptr<PhysicsObjects> genMuonCollection);

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
  std::shared_ptr<NanoMuon> muon1;
  std::shared_ptr<NanoMuon> muon2;

  TVector3 Lxyz;
  float LxySigma;

  bool hasDSAMuon;
  bool hasPatMuon;
};

#endif /* NanoDimuonVertex_hpp */