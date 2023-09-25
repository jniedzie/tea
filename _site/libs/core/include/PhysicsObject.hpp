//  PhysicsObject.hpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#ifndef PhysicsObject_hpp
#define PhysicsObject_hpp

#include "Collection.hpp"
#include "Helpers.hpp"
#include "Multitype.hpp"

class PhysicsObject;
typedef Collection<std::shared_ptr<PhysicsObject>> PhysicsObjects;

class PhysicsObject {
 public:
  PhysicsObject(std::string originalCollection_);
  PhysicsObject() = default;
  virtual ~PhysicsObject() = default;

  void Reset();

  inline std::string GetOriginalCollection() { return originalCollection; }

  inline auto Get(std::string branchName) {
    if (valuesTypes.count(branchName) == 0) {
      throw Exception(("Trying to access incorrect physics object-level branch: " + branchName).c_str());
    }
    return Multitype(this, branchName);
  }

 private:
  inline UInt_t GetUint(std::string branchName) { return *valuesUint[branchName]; }
  inline Int_t GetInt(std::string branchName) { return *valuesInt[branchName]; }
  inline Bool_t GetBool(std::string branchName) { return *valuesBool[branchName]; }
  inline Float_t GetFloat(std::string branchName) { return *valuesFloat[branchName]; }
  inline ULong64_t GetULong(std::string branchName) { return *valuesUlong[branchName]; }
  inline UChar_t GetUChar(std::string branchName) { return *valuesUchar[branchName]; }

  // contains all branch names and corresponding types
  std::map<std::string, std::string> valuesTypes;

  std::map<std::string, UInt_t *> valuesUint;
  std::map<std::string, Int_t *> valuesInt;
  std::map<std::string, Bool_t *> valuesBool;
  std::map<std::string, Float_t *> valuesFloat;
  std::map<std::string, ULong64_t *> valuesUlong;
  std::map<std::string, UChar_t *> valuesUchar;

  std::string originalCollection;

  friend class EventReader;
  template <typename T>
  friend class Multitype;
};

#endif /* PhysicsObject_hpp */
