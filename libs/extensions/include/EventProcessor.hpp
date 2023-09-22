//  EventProcessor.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef EventProcessor_hpp
#define EventProcessor_hpp

#include "ConfigManager.hpp"
#include "Event.hpp"
#include "GenParticle.hpp"
#include "Helpers.hpp"
#include "PhysicsObject.hpp"

struct FinalState;

class EventProcessor {
 public:
  EventProcessor(std::string configPath = "");
  
  float GetMaxPt(std::shared_ptr<Event> event, std::string collectionName);
  float GetHt(std::shared_ptr<Event> event, std::string collectionName);

 protected:
  std::vector<std::string> triggerNames;
  std::map<std::string, std::pair<float, float>> eventSelections;
  
  void AddExtraCollections(std::shared_ptr<Event> event);

 private:
  std::unique_ptr<ConfigManager> config;

  std::vector<int> GetTopIndices(std::shared_ptr<Event> event);
  std::vector<int> GetBottomIndices(std::shared_ptr<Event> event);
};

#endif /* EventProcessor_hpp */
