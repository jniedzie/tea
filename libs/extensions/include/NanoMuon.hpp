//  NanoMuon.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef NanoMuon_hpp
#define NanoMuon_hpp

#include "Helpers.hpp"
#include "NanoGenParticle.hpp"
#include "PhysicsObject.hpp"
#include "ScaleFactorsManager.hpp"

class NanoMuon;
typedef Collection<std::shared_ptr<NanoMuon>> NanoMuons;
typedef std::pair<std::shared_ptr<NanoMuon>, std::shared_ptr<NanoMuon>> NanoMuonPair;
typedef Collection<NanoMuonPair> NanoMuonPairs;

class NanoMuon {
 public:
  NanoMuon(std::shared_ptr<PhysicsObject> physicsObject_);

  auto Get(std::string branchName, bool verbose = true, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, verbose, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) {
    return physicsObject->GetAs<T>(branchName);
  }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  std::shared_ptr<PhysicsObject> GetPhysicsObject() { return physicsObject; }

  bool IsDSA() { return GetOriginalCollection() == "DSAMuon"; };
  bool IsTight();

  inline float GetPt() { return physicsObject->Get("pt"); }
  inline float GetEta() { return physicsObject->Get("eta"); }
  inline float GetPhi() { return physicsObject->Get("phi"); }
  inline int GetCharge() { return physicsObject->GetAs<int>("charge"); }
  inline float GetOuterEta() { return physicsObject->Get("outerEta"); }
  inline float GetOuterPhi() { return physicsObject->Get("outerPhi"); }

  int GetMatchIdxForNthBestMatch(int N);
  int GetMatchesForNthBestMatch(int N);

  std::shared_ptr<NanoGenParticle> GetGenMuon(std::shared_ptr<PhysicsObjects> genMuonCollection, float maxDeltaR = 0.3);

  TLorentzVector GetFourVector();

  std::map<std::string, float> GetScaleFactors(std::string nameID, std::string nameIso, std::string nameReco, std::string year);

  MuonID GetID();
  MuonIso GetIso();

  float OuterDeltaRtoMuon(std::shared_ptr<NanoMuon> muon);

  void Print();

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
  std::map<std::string, float> scaleFactor;
};

#endif /* NanoMuon_hpp */
