#ifndef HepMCParticle_hpp
#define HepMCParticle_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class HepMCParticle;
typedef Collection<std::shared_ptr<HepMCParticle>> HepMCParticles;

class HepMCParticle : public std::enable_shared_from_this<HepMCParticle> {
 public:
  HepMCParticle(std::shared_ptr<PhysicsObject> physicsObject_, int index_);

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return physicsObject->GetAs<T>(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

  float GetPx() { return physicsObject->Get("px"); }
  float GetPy() { return physicsObject->Get("py"); }
  float GetPz() { return physicsObject->Get("pz"); }

  float GetX() { return physicsObject->Get("x"); }  // in mm
  float GetY() { return physicsObject->Get("y"); }  // in mm
  float GetZ() { return physicsObject->Get("z"); }  // in mm

  float GetEnergy() { return physicsObject->Get("energy"); }
  float GetMass() { return physicsObject->Get("mass"); }

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

  std::shared_ptr<HepMCParticle> GetMother(const std::shared_ptr<PhysicsObjects>& allParticles);

  std::vector<int>& GetDaughters() { return daughters; }

  TVector3 GetOrigin() { return TVector3(GetZ() / 1e3, GetX() / 1e3, GetY() / 1e3); }
  TVector3 GetMomentum() {
    auto fourVector = GetLorentzVector();
    float eta = fourVector.Eta();
    float phi = fourVector.Phi();
    TVector3 direction(std::sinh(eta), std::cos(phi), std::sin(phi));

    // rescale direction to the momentum magnitude
    direction *= 1 / direction.Mag();
    direction *= fourVector.P();

    return direction;
  }

 private:
  int index;

  std::vector<int> daughters;
  std::shared_ptr<PhysicsObject> physicsObject;

  void SetupDaughters();
};

#endif /* HepMCParticle_hpp */
