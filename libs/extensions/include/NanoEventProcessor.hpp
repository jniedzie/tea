//  NanoEventProcessor.hpp
//
//  Created by Jeremi Niedziela on 24/11/2023.

#ifndef NanoEventProcessor_hpp
#define NanoEventProcessor_hpp

#include "Event.hpp"
#include "ExtensionsHelpers.hpp"
#include "EventProcessor.hpp"
#include "NanoMuon.hpp"

class NanoEventProcessor {
 public:
  NanoEventProcessor();

  float GetGenWeight(const std::shared_ptr<NanoEvent> event);
  float GetPileupScaleFactor(const std::shared_ptr<NanoEvent> event, std::string name);
  float GetMuonTriggerScaleFactor(const std::shared_ptr<NanoEvent> event, std::string name);

  std::pair<std::shared_ptr<NanoMuon>, std::shared_ptr<NanoMuon>> GetMuonPairClosestToZ(const std::shared_ptr<NanoEvent> event, std::string collection);

 private:
 std::unique_ptr<EventProcessor> eventProcessor;
 
 std::string weightsBranchName;
};

#endif /* NanoEventProcessor_hpp */
