#ifndef TemplateName_hpp
#define TemplateName_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class TemplateName {
 public:
  TemplateName(std::shared_ptr<Event> event_) : event(event_) {}

  auto Get(std::string branchName, const char* file = __builtin_FILE(), const char* function = __builtin_FUNCTION(),
           int line = __builtin_LINE()) {
    return event->Get(branchName, file, function, line);
  }

  template <typename T>
  T GetAs(std::string branchName) { return event->GetAs<float>(branchName); }
  std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const { return event->GetCollection(name); }
  void AddExtraCollections() { event->AddExtraCollections(); }

 private:
  std::shared_ptr<Event> event;
};

#endif /* TemplateName_hpp */
