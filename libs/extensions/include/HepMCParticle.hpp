#ifndef HepMCParticle_hpp
#define HepMCParticle_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class HepMCParticle;
typedef Collection<std::shared_ptr<HepMCParticle>> HepMCParticles;

class HepMCParticle : public std::enable_shared_from_this<HepMCParticle> {
 public:
  HepMCParticle(std::shared_ptr<PhysicsObject> physicsObject_, int index_, int maxNdaughters_);

  auto Get(std::string branchName) { return physicsObject->Get(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  float GetPx() { return physicsObject->Get("px"); }
  float GetPy() { return physicsObject->Get("py"); }
  float GetPz() { return physicsObject->Get("pz"); }
  float GetEnergy() { return physicsObject->Get("energy"); }

  int GetStatus() { return physicsObject->Get("status"); }
  int GetPid() { return physicsObject->Get("pid"); }

  bool IsJPsi() { return abs(GetPid()) == 443 /* && GetStatus() == 2*/; }
  bool IsPion() { return abs(GetPid()) == 211 /* && GetStatus() == 1*/; }
  int GetCharge() { return GetPid() > 0 ? 1 : -1; }

  TLorentzVector GetLorentzVector() {
    TLorentzVector vec;
    vec.SetPxPyPzE(GetPx(), GetPy(), GetPz(), GetEnergy());
    return vec;
  }

  int GetIndex() { return index; }
  void SetIndex(int index_) { index = index_; }

  void SetMother(int mother_) { mother = mother_; }
  void AddMother(int mother_) { mothers.push_back(mother_); }
  int GetMother() { return mother; }
  std::vector<int>& GetMothers() { return mothers; }

  bool HasMother(int motherPid, const HepMCParticles& allParticles);
  bool IsMother(int motherPid, const HepMCParticles& allParticles);

  std::vector<int>& GetDaughters() { return daughters; }

 private:
  int maxNdaughters;
  int index;
  int mother;
  std::vector<int> daughters;
  std::vector<int> mothers;

  std::shared_ptr<PhysicsObject> physicsObject;

  void SetupDaughters();
};

#endif /* HepMCParticle_hpp */
