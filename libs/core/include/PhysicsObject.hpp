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
      throw Exception(message.c_str());
    }
    return Multitype(this, branchName);
  }

  template <typename T>
  T GetAs(std::string branchName) {
    if (defaultCollectionsTypes.count(branchName)) {
      std::string branchType = defaultCollectionsTypes[branchName];
      if (branchType == "Int_t") {
        Int_t value = Get(branchName);
        return value;
      }
      if (branchType == "Bool_t") {
        Bool_t value = Get(branchName);
        return value;
      }
      if (branchType == "Float_t") {
        Float_t value = Get(branchName);
        return value;
      }
      if (branchType == "UChar_t") {
        UChar_t value = Get(branchName);
        return value;
      }
      if (branchType == "UShort_t") {
        UShort_t value = Get(branchName);
        return value;
      }
      if (branchType == "Short_t") {
        Short_t value = Get(branchName);
        return value;
      }
      if (branchType == "UInt_t") {
        UInt_t value = Get(branchName);
        return value;
      }
    }

    try {
      Float_t value = Get(branchName);
      defaultCollectionsTypes[branchName] = "Float_t";
      return value;
    } catch (BadTypeException &e) {
      try {
        Int_t value = Get(branchName);
        defaultCollectionsTypes[branchName] = "Int_t";
        return value;
      } catch (BadTypeException &e) {
        try {
          UChar_t value = Get(branchName);
          defaultCollectionsTypes[branchName] = "UChar_t";
          return value;
        } catch (BadTypeException &e) {
          try {
            UShort_t value = Get(branchName);
            defaultCollectionsTypes[branchName] = "UShort_t";
            return value;
          } catch (BadTypeException &e) {
            try {
              Short_t value = Get(branchName);
              defaultCollectionsTypes[branchName] = "Short_t";
              return value;
            } catch (BadTypeException &e) {
              try {
                UInt_t value = Get(branchName);
                defaultCollectionsTypes[branchName] = "UInt_t";
                return value;
              } catch (BadTypeException &e) {
                try {
                  Bool_t value = Get(branchName);
                  defaultCollectionsTypes[branchName] = "Bool_t";
                  return value;
                } catch (BadTypeException &e) {
                  error() << "Couldn't get value for branch " << branchName << std::endl;
                }
              }
            }
          }
        }
      }
    }
    return 0;
  }

 private:
  inline UInt_t GetUint(std::string branchName) { return *valuesUint[branchName]; }
  inline Int_t GetInt(std::string branchName) { return *valuesInt[branchName]; }
  inline Bool_t GetBool(std::string branchName) { return *valuesBool[branchName]; }
  inline Float_t GetFloat(std::string branchName) { return *valuesFloat[branchName]; }
  inline ULong64_t GetULong(std::string branchName) { return *valuesUlong[branchName]; }
  inline UChar_t GetUChar(std::string branchName) { return *valuesUchar[branchName]; }
  inline UChar_t GetChar(std::string branchName) { return *valuesChar[branchName]; }
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
  std::map<std::string, Char_t *> valuesChar;
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
