//  NanoElectron.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef NanoElectron_hpp
#define NanoElectron_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class NanoElectron;
typedef Collection<std::shared_ptr<NanoElectron>> NanoElectrons;

class NanoElectron {
 public:
  NanoElectron(std::shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

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

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
};

#endif /* NanoElectron_hpp */
