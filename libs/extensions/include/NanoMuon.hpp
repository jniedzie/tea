//  NanoMuon.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef NanoMuon_hpp
#define NanoMuon_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"
#include "ScaleFactorsManager.hpp"

class NanoMuon;
typedef Collection<std::shared_ptr<NanoMuon>> NanoMuons;

class NanoMuon {
 public:
  NanoMuon(std::shared_ptr<PhysicsObject> physicsObject_);

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, file, function, line);
  }
  float GetAsFloat(std::string branchName) { return physicsObject->GetAsFloat(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  std::shared_ptr<PhysicsObject> GetPhysicsObject() { return physicsObject; }

  bool isDSAMuon() { return GetOriginalCollection() == "DSAMuon"; };

  inline float GetPt() { return physicsObject->Get("pt"); }
  inline float GetEta() { return physicsObject->Get("eta"); }
  inline float GetPhi() { return physicsObject->Get("phi"); }
  inline float GetOuterEta() { return physicsObject->Get("outerEta"); }
  inline float GetOuterPhi() { return physicsObject->Get("outerPhi"); }

  float GetMatchIdxForNthBestMatch(int N);
  float GetMatchesForNthBestMatch(int N);

  TLorentzVector GetFourVector();

  float GetScaleFactor(std::string nameID, std::string nameIso, std::string nameReco);

  MuonID GetID();
  MuonIso GetIso();

  float OuterDeltaRtoMuon(std::shared_ptr<NanoMuon> muon);

  void Print() {
    info() << "NanoMuon: pt=" << GetPt() << " eta=" << GetEta() << " phi=" << GetPhi() << std::endl;
    GetID().Print();
    GetIso().Print();
  }

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
  float scaleFactor = -1;
};

#endif /* NanoMuon_hpp */
