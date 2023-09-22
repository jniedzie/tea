//  GenParticle.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef GenParticle_hpp
#define GenParticle_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class GenParticle;
typedef Collection<std::shared_ptr<GenParticle>> GenParticles;

class GenParticle {
 public:
  GenParticle(std::shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

  int GetPdgId();
  int GetMotherIndex() { return physicsObject->Get("genPartIdxMother"); }
  int GetStatusFlags() { return physicsObject->Get("statusFlags"); }

  bool IsLastCopy() { return (GetStatusFlags() & isLastCopy); }
  bool IsFirstCopy() { return (GetStatusFlags() & isFirstCopy); }

  bool IsGoodBottomQuark(std::shared_ptr<GenParticle> mother);
  bool IsGoodUdscQuark(std::shared_ptr<GenParticle> mother);
  bool IsGoodLepton(std::shared_ptr<GenParticle> mother);

  bool IsJet();
  bool IsTop();

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
