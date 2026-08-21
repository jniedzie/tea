//  Event.hpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#ifndef Event_hpp
#define Event_hpp

#include "ConfigManager.hpp"
#include "Helpers.hpp"
#include "Logger.hpp"
#include "Multitype.hpp"
#include "PhysicsObject.hpp"

class Event {
 public:
  Event();
  ~Event();

  void Reset();

  inline auto Get(std::string branchName, const char *file = __builtin_FILE(),
                  const char *function = __builtin_FUNCTION(), int line = __builtin_LINE()) {
    if (valuesTypes.count(branchName) == 0 && customValuesTypes.count(branchName) == 0) {
      std::string message = "\nTrying to access incorrect event-level branch: " + branchName;
      if (branchName.find("Weight") != std::string::npos || branchName.find("Wgt") != std::string::npos ||
          branchName.find("weight") != std::string::npos || branchName.find("wgt") != std::string::npos) {
        message += ", it's probably fine for data if this is a gen weight branch.";
        warn() << message << std::endl;
      } else
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

  inline std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const {
    if (collections.count(name)) return collections.at(name);
    if (extraCollections.count(name)) return extraCollections.at(name);
    std::string message = "Tried to get a collection that doesn't exist: " + name;
    throw Exception(message.c_str());
  }

  void AddExtraCollections();
  void AddCollection(std::string name, std::shared_ptr<PhysicsObjects> collection) {
    extraCollections.insert({name, collection});
  }
  void ReplaceCollection(std::string name, std::shared_ptr<PhysicsObjects> collection) {
    extraCollections[name] = collection;
  }

  const insertion_ordered_map<std::string, ExtraCollection> &GetExtraCollectionsDescriptions() const {
    return extraCollectionsDescriptions;
  }

  Int_t *GetIntVector(std::string branchName) { return valuesIntVector.at(branchName); }
  Bool_t *GetBoolVector(std::string branchName) { return valuesBoolVector.at(branchName); }
  Float_t *GetFloatVector(std::string branchName) { return valuesFloatVector.at(branchName); }
  Double_t *GetDoubleVector(std::string branchName) { return valuesDoubleVector.at(branchName); }
  UChar_t *GetUcharVector(std::string branchName) { return valuesUcharVector.at(branchName); }
  Char_t *GetCharVector(std::string branchName) { return valuesCharVector.at(branchName); }
  UInt_t *GetUintVector(std::string branchName) { return valuesUintVector.at(branchName); }
  UShort_t *GetUshortVector(std::string branchName) { return valuesUshortVector.at(branchName); }
  Short_t *GetShortVector(std::string branchName) { return valuesShortVector.at(branchName); }
  std::vector<unsigned int> *GetStdUintVector(std::string branchName) { return valuesStdUintVector.at(branchName); }

  template <typename T>
  void Set(const std::string &branchName, T value) {
    if constexpr (std::is_same_v<T, Float_t>)
      customValuesFloat[branchName] = value;
    else if constexpr (std::is_same_v<T, Double_t>)
      customValuesDouble[branchName] = value;
    else if constexpr (std::is_same_v<T, Int_t>)
      customValuesInt[branchName] = value;
    else if constexpr (std::is_same_v<T, UInt_t>)
      customValuesUint[branchName] = value;
    else if constexpr (std::is_same_v<T, Bool_t>)
      customValuesBool[branchName] = value;
    else if constexpr (std::is_same_v<T, ULong64_t>)
      customValuesUlong[branchName] = value;
    else if constexpr (std::is_same_v<T, UChar_t>)
      customValuesUchar[branchName] = value;
    else if constexpr (std::is_same_v<T, Short_t>)
      customValuesShort[branchName] = value;
    else if constexpr (std::is_same_v<T, UShort_t>)
      customValuesUshort[branchName] = value;
    else
      static_assert(!sizeof(T), "Event::Set<T>: unsupported type");

    customValuesTypes[branchName] = RootTypeName<T>();
  }

  template <typename T>
  void SetVector(const std::string &branchName, std::vector<T> value) {
    if constexpr (std::is_same_v<T, Float_t>)
      customValuesVectorFloat[branchName] = std::move(value);
    else if constexpr (std::is_same_v<T, Double_t>)
      customValuesVectorDouble[branchName] = std::move(value);
    else if constexpr (std::is_same_v<T, Int_t>)
      customValuesVectorInt[branchName] = std::move(value);
    else if constexpr (std::is_same_v<T, UInt_t>)
      customValuesVectorUInt[branchName] = std::move(value);
    else
      static_assert(!sizeof(T), "Event::SetVector<T>: unsupported type (Float_t, Double_t, Int_t, UInt_t only)");

    customValuesTypes[branchName] = "vector<" + std::string(RootTypeName<T>()) + ">";
  }

  template <typename T>
  const std::vector<T> &GetVector(const std::string &branchName) const {
    std::string expectedType = "vector<" + std::string(RootTypeName<T>()) + ">";
    auto typeIt = customValuesTypes.find(branchName);
    if (typeIt == customValuesTypes.end() || typeIt->second != expectedType) {
      std::string message = "Casting a custom vector branch " + branchName + " (" +
                            (typeIt == customValuesTypes.end() ? std::string("not set") : typeIt->second) + ") to " +
                            expectedType + "\n";
      throw BadTypeException(message.c_str());
    }
    if constexpr (std::is_same_v<T, Float_t>)
      return customValuesVectorFloat.at(branchName);
    else if constexpr (std::is_same_v<T, Double_t>)
      return customValuesVectorDouble.at(branchName);
    else if constexpr (std::is_same_v<T, Int_t>)
      return customValuesVectorInt.at(branchName);
    else if constexpr (std::is_same_v<T, UInt_t>)
      return customValuesVectorUInt.at(branchName);
    else
      static_assert(!sizeof(T), "Event::GetVector<T>: unsupported type (Float_t, Double_t, Int_t, UInt_t only)");
  }

  bool HasCustomValue(const std::string &branchName) const {
    return customValuesTypes.find(branchName) != customValuesTypes.end();
  }

 private:
  ConfigManager &config = ConfigManager::GetInstance();

  inline UInt_t GetUint(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesUint[branchName];
    return customValuesUint[branchName];
  }
  inline Int_t GetInt(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesInt[branchName];
    return customValuesInt[branchName];
  }
  inline Bool_t GetBool(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesBool[branchName];
    return customValuesBool[branchName];
  }
  inline Float_t GetFloat(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesFloat[branchName];
    return customValuesFloat[branchName];
  }
  inline Double_t GetDouble(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesDouble[branchName];
    return customValuesDouble[branchName];
  }
  inline ULong64_t GetULong(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesUlong[branchName];
    return customValuesUlong[branchName];
  }
  inline UChar_t GetUChar(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesUchar[branchName];
    return customValuesUchar[branchName];
  }
  inline Char_t GetChar(std::string branchName) { return valuesChar[branchName]; }
  inline UShort_t GetUShort(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesUshort[branchName];
    return customValuesUshort[branchName];
  }
  inline Short_t GetShort(std::string branchName) {
    if (valuesTypes.find(branchName) != valuesTypes.end()) return valuesShort[branchName];
    return customValuesShort[branchName];
  }

  std::map<std::string, std::string> valuesTypes;  /// contains all branch names and corresponding types
  std::map<std::string, std::string> customValuesTypes;

  std::map<std::string, UInt_t> valuesUint;
  std::map<std::string, Int_t> valuesInt;
  std::map<std::string, Bool_t> valuesBool;
  std::map<std::string, Float_t> valuesFloat;
  std::map<std::string, Float_t> customValuesFloat;
  std::map<std::string, Double_t> valuesDouble;
  std::map<std::string, Double_t> customValuesDouble;
  std::map<std::string, Int_t> customValuesInt;
  std::map<std::string, UInt_t> customValuesUint;
  std::map<std::string, Bool_t> customValuesBool;
  std::map<std::string, ULong64_t> customValuesUlong;
  std::map<std::string, UChar_t> customValuesUchar;
  std::map<std::string, Short_t> customValuesShort;
  std::map<std::string, UShort_t> customValuesUshort;
  std::map<std::string, std::vector<Float_t>> customValuesVectorFloat;
  std::map<std::string, std::vector<Double_t>> customValuesVectorDouble;
  std::map<std::string, std::vector<Int_t>> customValuesVectorInt;
  std::map<std::string, std::vector<UInt_t>> customValuesVectorUInt;
  std::map<std::string, ULong64_t> valuesUlong;
  std::map<std::string, UChar_t> valuesUchar;
  std::map<std::string, Char_t> valuesChar;
  std::map<std::string, UShort_t> valuesUshort;
  std::map<std::string, Short_t> valuesShort;

  std::map<std::string, Int_t[maxCollectionElements]> valuesIntVector;
  std::map<std::string, Bool_t[maxCollectionElements]> valuesBoolVector;
  std::map<std::string, Float_t[maxCollectionElements]> valuesFloatVector;
  std::map<std::string, Double_t[maxCollectionElements]> valuesDoubleVector;
  std::map<std::string, UChar_t[maxCollectionElements]> valuesUcharVector;
  std::map<std::string, Char_t[maxCollectionElements]> valuesCharVector;
  std::map<std::string, UInt_t[maxCollectionElements]> valuesUintVector;
  std::map<std::string, UShort_t[maxCollectionElements]> valuesUshortVector;
  std::map<std::string, Short_t[maxCollectionElements]> valuesShortVector;

  std::map<std::string, std::vector<float> *> valuesStdFloatVector;
  std::map<std::string, std::vector<double> *> valuesStdDoubleVector;
  std::map<std::string, std::vector<int> *> valuesStdIntVector;
  std::map<std::string, std::vector<unsigned int> *> valuesStdUintVector;

  std::map<std::string, std::shared_ptr<PhysicsObjects>> collections;
  std::map<std::string, std::shared_ptr<PhysicsObjects>> extraCollections;

  bool hasExtraCollections = true;
  insertion_ordered_map<std::string, ExtraCollection> extraCollectionsDescriptions;
  std::map<std::string, std::string> defaultCollectionsTypes;
  std::map<std::string, std::pair<unsigned, unsigned>> runRangesPerEra;

  friend class EventReader;
  template <typename T>
  friend class Multitype;

  template <typename First, typename... Rest>
  bool tryGet(std::shared_ptr<PhysicsObject> physicsObject, std::string branchName, std::pair<float, float> cuts);

  bool checkCuts(std::shared_ptr<PhysicsObject> physicsObject, std::string branchName, std::pair<float, float> cuts);
};

#endif /* Event_hpp */
