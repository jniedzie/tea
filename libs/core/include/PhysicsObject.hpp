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
  PhysicsObject(std::string originalCollection_, int index_ = -1);
  PhysicsObject() = default;
  virtual ~PhysicsObject() = default;

  void Reset();

  inline std::string GetOriginalCollection() { return originalCollection; }

  inline void SetIndex(int index_) { index = index_; }
  inline int GetIndex() { return index; }

  inline auto Get(std::string branchName, const char *file = __builtin_FILE(), const char *function = __builtin_FUNCTION(),
                  int line = __builtin_LINE()) {
    if (valuesTypes.count(branchName) == 0) {
      std::string message = "Trying to access incorrect physics object-level branch: ";
      message += branchName + " from " + originalCollection + " collection";

      fatal(file, function, line) << message << std::endl;
      exit(0);
    }
    return Multitype(this, branchName);
  }

  float GetAsFloat(std::string branchName);

 private:
  inline UInt_t GetUint(std::string branchName) { return *valuesUint[branchName]; }
  inline Int_t GetInt(std::string branchName) { return *valuesInt[branchName]; }
  inline Bool_t GetBool(std::string branchName) { return *valuesBool[branchName]; }
  inline Float_t GetFloat(std::string branchName) { return *valuesFloat[branchName]; }
  inline ULong64_t GetULong(std::string branchName) { return *valuesUlong[branchName]; }
  inline UChar_t GetUChar(std::string branchName) { return *valuesUchar[branchName]; }
  inline UShort_t GetUShort(std::string branchName) { return *valuesUshort[branchName]; }
  inline Short_t GetShort(std::string branchName) { return *valuesShort[branchName]; }

  // contains all branch names and corresponding types
  std::map<std::string, std::string> valuesTypes;

  std::map<std::string, UInt_t *> valuesUint;
  std::map<std::string, Int_t *> valuesInt;
  std::map<std::string, Bool_t *> valuesBool;
  std::map<std::string, Float_t *> valuesFloat;
  std::map<std::string, ULong64_t *> valuesUlong;
  std::map<std::string, UChar_t *> valuesUchar;
  std::map<std::string, UShort_t *> valuesUshort;
  std::map<std::string, Short_t *> valuesShort;

  std::string originalCollection;
  int index;
  std::map<std::string, std::string> defaultCollectionsTypes;

  friend class EventReader;
  template <typename T>
  friend class Multitype;
};

#endif /* PhysicsObject_hpp */
