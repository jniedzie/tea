//  Multitype.hpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#ifndef Multitype_hpp
#define Multitype_hpp

#include "Helpers.hpp"

template <typename T>
class Multitype {
 public:
  Multitype(T *object_, std::string branchName_) : object(object_), branchName(branchName_) {}

  operator UInt_t() {
    if (!isCorrectType("UInt_t")) return 0;
    return object->GetUint(branchName);
  }
  operator Int_t() {
    if (!isCorrectType("Int_t")) return 0;
    return object->GetInt(branchName);
  }
  operator Bool_t() {
    if (!isCorrectType("Bool_t")) return 0;
    return object->GetBool(branchName);
  }
  operator Float_t() {
    if (!isCorrectType("Float_t")) return 0;
    return object->GetFloat(branchName);
    ;
  }
  operator ULong64_t() {
    if (!isCorrectType("ULong64_t")) return 0;
    return object->GetULong(branchName);
  }
  operator UChar_t() {
    if (!isCorrectType("UChar_t")) return 0;
    return object->GetUChar(branchName);
  }

 private:
  T *object;
  std::string branchName;

  bool isCorrectType(std::string typeName) {
    std::string branchType = object->valuesTypes.at(branchName);
    if (branchType != typeName) {
      warn() << "Casting a physics object-level branch " << branchName;
      warn() << " (" << branchType << ") to " << typeName << "\n";
      return false;
    }
    return true;
  }
};

#endif /* Multitype_hpp */