//  Event.hpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#ifndef Event_hpp
#define Event_hpp

#include "Helpers.hpp"
#include "Multitype.hpp"
#include "PhysicsObject.hpp"
#include "Logger.hpp"

class Event {
 public:
  Event();
  ~Event();

  void Reset();

  inline auto Get(std::string branchName) {
    if (valuesTypes.count(branchName) == 0) {
      throw Exception(("Trying to access incorrect event-level branch: " + branchName).c_str());
    }

    return Multitype(this, branchName);
  }

  inline std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const {
    if (collections.count(name)) return collections.at(name);
    if (extraCollections.count(name)) return extraCollections.at(name);
    fatal() << "Tried to get a collection that doesn't exist: " << name << "\n";
    exit(1);
  }

  inline int GetCollectionSize(std::string name) {
    if (collections.count(name)) return collections.at(name)->size();
    if (extraCollections.count(name)) return extraCollections.at(name)->size();
    fatal() << "Tried to get a collection that doesn't exist: " << name << "\n";
    exit(1);
  }

  inline void AddExtraCollection(std::string name, std::shared_ptr<PhysicsObjects> collection) {
    

    extraCollections.insert({name, collection});
  }

 private:
  inline UInt_t GetUint(std::string branchName) { return valuesUint[branchName]; }
  inline Int_t GetInt(std::string branchName) { return valuesInt[branchName]; }
  inline Bool_t GetBool(std::string branchName) { return valuesBool[branchName]; }
  inline Float_t GetFloat(std::string branchName) { return valuesFloat[branchName]; }
  inline ULong64_t GetULong(std::string branchName) { return valuesUlong[branchName]; }
  inline UChar_t GetUChar(std::string branchName) { return valuesUchar[branchName]; }

  std::map<std::string, std::string> valuesTypes;  /// contains all branch names and corresponding types

  std::map<std::string, UInt_t> valuesUint;
  std::map<std::string, Int_t> valuesInt;
  std::map<std::string, Bool_t> valuesBool;
  std::map<std::string, Float_t> valuesFloat;
  std::map<std::string, ULong64_t> valuesUlong;
  std::map<std::string, UChar_t> valuesUchar;

  std::map<std::string, Int_t[maxCollectionElements]> valuesIntVector;
  std::map<std::string, Bool_t[maxCollectionElements]> valuesBoolVector;
  std::map<std::string, Float_t[maxCollectionElements]> valuesFloatVector;
  std::map<std::string, UChar_t[maxCollectionElements]> valuesUcharVector;

  std::map<std::string, std::shared_ptr<PhysicsObjects>> collections;
  std::map<std::string, std::shared_ptr<PhysicsObjects>> extraCollections;

  friend class EventReader;
  template <typename T>
  friend class Multitype;
};

#endif /* Event_hpp */
