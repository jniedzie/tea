#ifndef TemplateName_hpp
#define TemplateName_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class TemplateName {
 public:
  TemplateName(std::shared_ptr<Event> event_) : event(event_) {}

  auto Get(std::string branchName) { return event->Get(branchName); }
  std::shared_ptr<PhysicsObjects> GetCollection(std::string name) const { return event->GetCollection(name); }
  int GetCollectionSize(std::string name) { return event->GetCollectionSize(name); }
  void AddExtraCollection(std::string name, std::shared_ptr<PhysicsObjects> collection) { event->AddExtraCollection(name, collection); }

 private:
  std::shared_ptr<Event> event;
};

#endif /* TemplateName_hpp */
