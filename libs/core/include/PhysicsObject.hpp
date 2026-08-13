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
  // virtual ~PhysicsObject() = default;
  virtual ~PhysicsObject() {
    ForgetCustomValues();
    for (auto& [name, ptr] : customValuesFloat) delete ptr;
    for (auto& [name, ptr] : customValuesDouble) delete ptr;
    for (auto& [name, ptr] : customValuesInt) delete ptr;
    for (auto& [name, ptr] : customValuesUint) delete ptr;
    for (auto& [name, ptr] : customValuesBool) delete ptr;
    for (auto& [name, ptr] : customValuesUlong) delete ptr;
    for (auto& [name, ptr] : customValuesUchar) delete ptr;
    for (auto& [name, ptr] : customValuesShort) delete ptr;
    for (auto& [name, ptr] : customValuesUshort) delete ptr;
  }

  void Reset();

  inline std::string GetOriginalCollection() { return originalCollection; }

  inline void SetIndex(int index_) { index = index_; }
  inline int GetIndex() { return index; }

  inline auto Get(std::string branchName, bool verbose = true, const char *file = __builtin_FILE(),
                  const char *function = __builtin_FUNCTION(), int line = __builtin_LINE()) {
    if (valuesTypes.count(branchName) == 0 && customValuesTypes.count(branchName) == 0 ) {
      std::string message = "Trying to access incorrect physics object-level branch: ";
      message += branchName + " from " + originalCollection + " collection";

      if (verbose) fatal(file, function, line) << message << std::endl;
      throw Exception(message.c_str());
    }
    return Multitype(this, branchName);
  }

  inline TLorentzVector GetFourVector() {
    TLorentzVector vec;
    vec.SetPtEtaPhiM(GetAs<float>("pt"), GetAs<float>("eta"), GetAs<float>("phi"), GetAs<float>("mass"));
    return vec;
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
      if (branchType == "Double_t") {
        Double_t value = Get(branchName);
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
        Double_t value = Get(branchName);
        defaultCollectionsTypes[branchName] = "Double_t";
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
    }
    return 0;
  }

  template <typename T> void Set(const std::string &branchName, T value) {
    if constexpr (std::is_same_v<T, Float_t>) {
      auto it = customValuesFloat.find(branchName);
      if (it != customValuesFloat.end()) delete it->second;
      customValuesFloat[branchName] = new Float_t(value);
    } else if constexpr (std::is_same_v<T, Double_t>) {
      auto it = customValuesDouble.find(branchName);
      if (it != customValuesDouble.end()) delete it->second;
      customValuesDouble[branchName] = new Double_t(value);
    } else if constexpr (std::is_same_v<T, Int_t>) {
      auto it = customValuesInt.find(branchName);
      if (it != customValuesInt.end()) delete it->second;
      customValuesInt[branchName] = new Int_t(value);
    } else if constexpr (std::is_same_v<T, UInt_t>) {
      auto it = customValuesUint.find(branchName);
      if (it != customValuesUint.end()) delete it->second;
      customValuesUint[branchName] = new UInt_t(value);
    } else if constexpr (std::is_same_v<T, Bool_t>) {
      auto it = customValuesBool.find(branchName);
      if (it != customValuesBool.end()) delete it->second;
      customValuesBool[branchName] = new Bool_t(value);
    } else if constexpr (std::is_same_v<T, ULong64_t>) {
      auto it = customValuesUlong.find(branchName);
      if (it != customValuesUlong.end()) delete it->second;
      customValuesUlong[branchName] = new ULong64_t(value);
    } else if constexpr (std::is_same_v<T, UChar_t>) {
      auto it = customValuesUchar.find(branchName);
      if (it != customValuesUchar.end()) delete it->second;
      customValuesUchar[branchName] = new UChar_t(value);
    } else if constexpr (std::is_same_v<T, Short_t>) {
      auto it = customValuesShort.find(branchName);
      if (it != customValuesShort.end()) delete it->second;
      customValuesShort[branchName] = new Short_t(value);
    } else if constexpr (std::is_same_v<T, UShort_t>) {
      auto it = customValuesUshort.find(branchName);
      if (it != customValuesUshort.end()) delete it->second;
      customValuesUshort[branchName] = new UShort_t(value);
    } else {
      static_assert(!sizeof(T), "PhysicsObject::Set<T>: unsupported type");
    }

    customValuesTypes[branchName] = RootTypeName<T>();
    RememberCustomValues();
  }

  bool HasCustomValue(const std::string &branchName) const {
    return customValuesTypes.find(branchName) != customValuesTypes.end();
  }

  /// Custom values describe the current event only, but physics objects are allocated once and reused for every event,
  /// so a value set in one event would still look "set" in all following ones (and would be written out again by
  /// EventWriter). Called from Event::Reset(), it clears the type markers of the objects that were set since the last
  /// reset, which is all HasCustomValue() looks at.
  static void ClearAllCustomValues();

 private:
  /// Registers/unregisters this object in the list ClearAllCustomValues() walks
  void RememberCustomValues();
  void ForgetCustomValues();

  bool hasCustomValues = false;

  inline UInt_t GetUint(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesUint[branchName];
    return *customValuesUint[branchName];
  }
  inline Int_t GetInt(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesInt[branchName];
    return *customValuesInt[branchName];
  }
  inline Bool_t GetBool(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesBool[branchName];
    return *customValuesBool[branchName];
  }
  inline Float_t GetFloat(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end())
      return *valuesFloat[branchName];
    return *customValuesFloat[branchName];
  }
  inline Double_t GetDouble(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesDouble[branchName];
    return *customValuesDouble[branchName];
  }
  inline ULong64_t GetULong(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesUlong[branchName];
    return *customValuesUlong[branchName];
  }
  inline UChar_t GetUChar(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesUchar[branchName];
    return *customValuesUchar[branchName];
  }
  inline UChar_t GetChar(std::string branchName) { return *valuesChar[branchName]; }
  inline UShort_t GetUShort(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesUshort[branchName];
    return *customValuesUshort[branchName];
  }
  inline Short_t GetShort(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return *valuesShort[branchName];
    return *customValuesShort[branchName];
  }

  // contains all branch names and corresponding types
  std::map<std::string, std::string> valuesTypes;
  std::map<std::string, std::string> customValuesTypes;

  std::map<std::string, UInt_t *> valuesUint;
  std::map<std::string, Int_t *> valuesInt;
  std::map<std::string, Bool_t *> valuesBool;
  std::map<std::string, Float_t *> valuesFloat;
  std::map<std::string, Double_t *> valuesDouble;
  std::map<std::string, ULong64_t *> valuesUlong;
  std::map<std::string, UChar_t *> valuesUchar;
  std::map<std::string, Char_t *> valuesChar;
  std::map<std::string, UShort_t *> valuesUshort;
  std::map<std::string, Short_t *> valuesShort;

  std::map<std::string, Float_t*> customValuesFloat;
  std::map<std::string, Double_t*> customValuesDouble;
  std::map<std::string, Int_t*> customValuesInt;
  std::map<std::string, UInt_t*> customValuesUint;
  std::map<std::string, Bool_t*> customValuesBool;
  std::map<std::string, ULong64_t*> customValuesUlong;
  std::map<std::string, UChar_t*> customValuesUchar;
  std::map<std::string, Short_t*> customValuesShort;
  std::map<std::string, UShort_t*> customValuesUshort;

  std::string originalCollection;
  int index;
  std::map<std::string, std::string> defaultCollectionsTypes;

  friend class EventReader;
  template <typename T>
  friend class Multitype;
};

#endif /* PhysicsObject_hpp */
