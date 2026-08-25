//  HistogramsFiller.hpp
//
//  Created by Jeremi Niedziela on 10/08/2023.

#ifndef HistogramsFiller_hpp
#define HistogramsFiller_hpp

#include "CutFlowManager.hpp"
#include "Event.hpp"
#include "Helpers.hpp"
#include "HistogramsHandler.hpp"

class HistogramsFiller {
 public:
  HistogramsFiller(std::shared_ptr<HistogramsHandler> histogramsHandler_);
  ~HistogramsFiller();

  void FillDefaultVariables(const std::shared_ptr<Event> event);

  void FillCutFlow(const std::shared_ptr<CutFlowManager> cutFlowManager);

 private:
  std::shared_ptr<HistogramsHandler> histogramsHandler;
  std::map<std::string, HistogramParams> defaultHistVariables;
  std::string weightsBranchName;

  std::map<std::string, std::string> defaultCollectionsTypes;

  template <typename T>
  float GetValue(std::shared_ptr<T> object, std::string branchName);
};

#endif /* HistogramsFiller_hpp */
