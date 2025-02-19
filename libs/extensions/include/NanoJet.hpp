//  Jet.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef Jet_hpp
#define Jet_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class NanoJet;
typedef Collection<std::shared_ptr<NanoJet>> NanoJets;

class NanoJet {
 public:
  NanoJet(std::shared_ptr<PhysicsObject> physicsObject_);

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return physicsObject->GetAs<T>(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  inline float GetPt() { return physicsObject->Get("pt"); }
  inline float GetEta() { return physicsObject->Get("eta"); }
  inline float GetPhi() { return physicsObject->Get("phi"); }
  inline float GetMass() { return physicsObject->Get("mass"); }
  inline float GetDeepCSVscore() { return physicsObject->Get("btagDeepB"); }
  inline float GetDeepJetScore() { return physicsObject->Get("btagDeepFlavB"); }

  TLorentzVector GetFourVector();

  float GetBtaggingScaleFactor(std::string workingPoint);
  float GetJetIDScaleFactor(std::string name);

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
};

#endif /* Jet_hpp */
