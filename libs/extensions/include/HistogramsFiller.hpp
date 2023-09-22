//  HistogramsFiller.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef HistogramsFiller_hpp
#define HistogramsFiller_hpp

#include "Event.hpp"
#include "Helpers.hpp"
#include "HistogramsHandler.hpp"
#include "CutFlowManager.hpp"
#include "EventProcessor.hpp"

class HistogramsFiller {
 public:
  HistogramsFiller(std::string configPath, std::shared_ptr<HistogramsHandler> histogramsHandler_);
  ~HistogramsFiller();

  void FillDefaultVariables(const std::shared_ptr<Event> event);

  void FillCutFlow(const std::shared_ptr<CutFlowManager> cutFlowManager);  

 private:
  std::shared_ptr<HistogramsHandler> histogramsHandler;
  std::unique_ptr<EventProcessor> eventProcessor;

  std::map<std::string, std::vector<std::string>> defaultHistVariables;

};

#endif /* HistogramsFiller_hpp */
