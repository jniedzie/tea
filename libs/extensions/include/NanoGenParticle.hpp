//  NanoGenParticle.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef GenParticle_hpp
#define GenParticle_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class NanoGenParticle;
typedef Collection<std::shared_ptr<NanoGenParticle>> GenParticles;

class NanoGenParticle {
 public:
  NanoGenParticle(std::shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return physicsObject->GetAs<T>(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  TLorentzVector GetFourVector(float mass);
  float GetMass() { return physicsObject->Get("mass"); }
  float GetPt() { return physicsObject->Get("pt"); }
  int GetPdgId() { return physicsObject->Get("pdgId"); }
  int GetMotherIndex() { return physicsObject->Get("genPartIdxMother"); }
  int GetStatusFlags() { return physicsObject->GetAs<int>("statusFlags"); }
  float GetDxy(float pv_x, float pv_y);

  bool IsLastCopy() { return (GetStatusFlags() & isLastCopy); }
  bool IsFirstCopy() { return (GetStatusFlags() & isFirstCopy); }

  bool IsGoodBottomQuark(std::shared_ptr<NanoGenParticle> mother);
  bool IsGoodUdscQuark(std::shared_ptr<NanoGenParticle> mother);
  bool IsGoodLepton(std::shared_ptr<NanoGenParticle> mother);
  bool IsGoodParticleWithID(int pdgId);

  bool IsJet();
  bool IsTop();
  bool IsMuon();

  std::shared_ptr<NanoGenParticle> GetFirstCopy(std::shared_ptr<PhysicsObjects> genParticles);

 private:
  std::shared_ptr<PhysicsObject> physicsObject;

  enum StatusFlagMask {
    isPrompt = 1 << 0,
    isDecayedLeptonHadron = 1 << 1,
    isTauDecayProduct = 1 << 2,
    isPromptTauDecayProduct = 1 << 3,
    isDirectTauDecayProduct = 1 << 4,
    isDirectPromptTauDecayProduct = 1 << 5,
    isDirectHadronDecayProduct = 1 << 6,
    isHardProcess = 1 << 7,
    fromHardProcess = 1 << 8,
    isHardProcessTauDecayProduct = 1 << 9,
    isDirectHardProcessTauDecayProduct = 1 << 10,
    fromHardProcessBeforeFSR = 1 << 11,
    isFirstCopy = 1 << 12,
    isLastCopy = 1 << 13,
    isLastCopyBeforeFSR = 1 << 14
  };
};

#endif /* GenParticle_hpp */
