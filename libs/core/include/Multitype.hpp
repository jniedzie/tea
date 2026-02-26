//  Multitype.hpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#ifndef Multitype_hpp
#define Multitype_hpp

#include "Helpers.hpp"

// Define custom exception class
class BadTypeException : public std::exception {
 public:
  BadTypeException(const char *message) : msg_(message) {}
  ~BadTypeException() {}
  const char *what() const noexcept { return msg_.c_str(); }

 private:
  std::string msg_;
};

template <typename T>
class Multitype {
 public:
  Multitype(T *object_, std::string branchName_) : object(object_), branchName(branchName_) {}

  operator UInt_t() {
    checkType("UInt_t");
    return object->GetUint(branchName);
  }
  operator Int_t() {
    checkType("Int_t");
    return object->GetInt(branchName);
  }
  operator Bool_t() {
    checkType("Bool_t");
    return object->GetBool(branchName);
  }
  operator Float_t() {
    checkType("Float_t");
    return object->GetFloat(branchName);
  }
  operator ULong64_t() {
    checkType("ULong64_t");
    return object->GetULong(branchName);
  }
  operator UChar_t() {
    checkType("UChar_t");
    return object->GetUChar(branchName);
  }
  operator UShort_t() {
    checkType("UShort_t");
    return object->GetUShort(branchName);
  }
  operator Short_t() {
    checkType("Short_t");
    return object->GetShort(branchName);
  }

 private:
  T *object;
  std::string branchName;

  void checkType(std::string typeName) {
    std::string branchType;
    if (object->valuesTypes.find(branchName) != object->valuesTypes.end()) 
      branchType = object->valuesTypes.at(branchName);
    else if (object->customValuesTypes.find(branchName) != object->customValuesTypes.end()) 
      branchType = object->customValuesTypes.at(branchName);
    else {
      std::string message = "Branch not found: " + branchName + "\n";
      throw BadTypeException(message.c_str());
    }
    if (branchType != typeName) {
      std::string message = "Casting a physics object-level branch " + branchName + " (" + branchType + ") to " + typeName + "\n";
      throw BadTypeException(message.c_str());
    }
  }
};

#endif /* Multitype_hpp */