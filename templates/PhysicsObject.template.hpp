#ifndef TemplateName_hpp
#define TemplateName_hpp

#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class TemplateName;
typedef Collection<std::shared_ptr<TemplateName>> TemplateNames;

class TemplateName {
 public:
  TemplateName(std::shared_ptr<PhysicsObject> physicsObject_) : physicsObject(physicsObject_) {}

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return physicsObject->Get(branchName, file, function, line);
  }
  float GetAsFloat(std::string branchName) { return physicsObject->GetAsFloat(branchName); }
  std::string GetOriginalCollection() { return physicsObject->GetOriginalCollection(); }
  void Reset() { physicsObject->Reset(); }

 private:
  std::shared_ptr<PhysicsObject> physicsObject;
};

#endif /* TemplateName_hpp */
