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

  float GetHt(std::shared_ptr<Event> event, std::string collectionName);

  void RegisterCuts(std::shared_ptr<CutFlowManager> cutFlowManager);

  bool PassesGoldenJson(const std::shared_ptr<Event> event);

  bool PassesTriggerSelections(const std::shared_ptr<Event> event);
  bool PassesMetFilters(const std::shared_ptr<Event> event);

  bool PassesEventSelections(const std::shared_ptr<Event> event, std::shared_ptr<CutFlowManager> cutFlowManager);

 private:
  std::vector<std::string> triggerNames;
  std::vector<std::pair<std::string, std::pair<float, float>>> eventSelections;
  std::vector<std::string> requiredFlags;

  std::map<int, std::vector<std::vector<int>>> goldenJson;

  std::vector<std::string> triggerWarningsPrinted;
};

#endif /* EventProcessor_hpp */
