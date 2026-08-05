//  Jet.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef Jet_hpp
#define Jet_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"
#include "NanoEvent.hpp"

class NanoJet;
typedef Collection<std::shared_ptr<NanoJet>> NanoJets;

class NanoJet {
 public:
  NanoJet(std::shared_ptr<PhysicsObject> physicsObject_);

  auto Get(std::string branchName, bool verbose = true, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, verbose, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return physicsObject->GetAs<T>(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  inline float GetPt() { return physicsObject->Get("pt"); }
  inline float GetEta() { return physicsObject->Get("eta"); }
  inline float GetAbsEta() { return fabs(float(physicsObject->Get("eta"))); }
  inline float GetPhi() { return physicsObject->Get("phi"); }
  inline float GetMass() { return physicsObject->Get("mass"); }
  inline float GetArea() { return physicsObject->Get("area"); }
  inline float GetDeepCSVscore() { return physicsObject->Get("btagDeepB"); }
  inline float GetDeepJetScore() { return physicsObject->Get("btagDeepFlavB"); }

  TLorentzVector GetFourVector();

  std::map<std::string,float> GetBtaggingScaleFactors(std::string workingPoint);
  std::map<std::string,float> GetPUJetIDScaleFactors(std::string name);
  std::map<std::string,float> GetJetEnergyCorrections(float rho);
  void AddSmearedPtByResolution(float rho, int eventID, std::shared_ptr<NanoEvent> event);

  float GetPxDifference(float newJetPt, float oldJetPt = -1);
  float GetPyDifference(float newJetPt, float oldJetPt = -1);

  bool IsInCollection(const std::shared_ptr<PhysicsObjects> collection);

 private:
  std::shared_ptr<PhysicsObject> physicsObject;

  std::shared_ptr<PhysicsObject> GetGenJetAsRecommendedForJER(std::shared_ptr<NanoEvent> event, float sigma_JER, float R_cone = 0.4);

};

#endif /* Jet_hpp */
