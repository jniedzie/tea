//  EventProcessor.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef EventProcessor_hpp
#define EventProcessor_hpp

#include "ConfigManager.hpp"
#include "CutFlowManager.hpp"
#include "Event.hpp"
#include "Helpers.hpp"
#include "PhysicsObject.hpp"

class EventProcessor {
 public:
  EventProcessor();
  
  float GetMaxPt(std::shared_ptr<Event> event, std::string collectionName);
  std::shared_ptr<PhysicsObject> GetMaxPtObject(std::shared_ptr<Event> event, std::string collectionName);
  std::shared_ptr<PhysicsObject> GetMaxPtObject(std::shared_ptr<Event> event, std::shared_ptr<PhysicsObjects> collection);
  std::shared_ptr<PhysicsObject> GetSubleadingPtObject(std::shared_ptr<Event> event, std::string collectionName);

  std::shared_ptr<PhysicsObjects> GetLeadingObjects(std::shared_ptr<Event> event, std::string collectionName, size_t numObjects);

  float GetHt(std::shared_ptr<Event> event, std::string collectionName);

  void RegisterCuts(std::shared_ptr<CutFlowManager> cutFlowManager);

  bool PassesGoldenJson(const std::shared_ptr<Event> event);

  bool PassesTriggerCuts(const std::shared_ptr<Event> event);
  bool PassesMetFilters(const std::shared_ptr<Event> event);

  bool PassesEventCuts(const std::shared_ptr<Event> event, std::shared_ptr<CutFlowManager> cutFlowManager=nullptr);

 private:
  std::vector<std::string> triggerNames;
  std::vector<std::pair<std::string, std::pair<float, float>>> eventCuts;
  std::vector<std::string> requiredFlags;

  std::map<int, std::vector<std::vector<int>>> goldenJson;

  std::vector<std::string> triggerWarningsPrinted;
};

#endif /* EventProcessor_hpp */
