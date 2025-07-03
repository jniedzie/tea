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
  std::map<std::string,float> GetMuonTriggerScaleFactors(const std::shared_ptr<NanoEvent> event, std::string name);
  std::map<std::string,float> GetMediumBTaggingScaleFactors(const std::shared_ptr<NanoJets> b_jets);
  std::map<std::string,float> GetPUJetIDScaleFactors(const std::shared_ptr<NanoJets> jets);
  std::map<std::string,float> GetMuonScaleFactors(const std::shared_ptr<NanoMuons> looseMuonCollection);

  std::pair<std::shared_ptr<NanoMuon>, std::shared_ptr<NanoMuon>> GetMuonPairClosestToZ(const std::shared_ptr<NanoEvent> event, std::string collection);

  bool IsDataEvent(const std::shared_ptr<NanoEvent> event);

  float PropagateMET(const std::shared_ptr<NanoEvent> event, float totalDeltaPx, float totalDeltaPy);

 private:
 std::unique_ptr<EventProcessor> eventProcessor;
 
 std::string weightsBranchName;
 std::string year;
};

#endif /* NanoEventProcessor_hpp */
