#ifndef TemplateName_hpp
#define TemplateName_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class TemplateName {
 public:
  TemplateName(std::shared_ptr<Event> event_) : event(event_) {}

  auto Get(std::string branchName) { return event->Get(branchName); }
  float GetAsFloat(std::string branchName) { return event->GetAsFloat(branchName); }
  std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const { return event->GetCollection(name); }
  void AddExtraCollections() { event->AddExtraCollections(); }

 private:
  std::shared_ptr<Event> event;
};

#endif /* TemplateName_hpp */
