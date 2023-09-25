//  CutFlowManager.hpp
//
//  Created by Jeremi Niedziela on 16/08/2023.

#ifndef CutFlowManager_hpp
#define CutFlowManager_hpp

#include "EventWriter.hpp"
#include "EventReader.hpp"
#include "Helpers.hpp"

class CutFlowManager;

class CutFlowManager {
 public:
  CutFlowManager(std::shared_ptr<EventReader> eventReader_, std::shared_ptr<EventWriter> eventWriter_=nullptr);
  ~CutFlowManager();

  void UpdateCutFlow(std::string cutName);
  void SaveCutFlow();
  std::map<std::string, float> GetCutFlow();

 private:
  std::shared_ptr<EventReader> eventReader;
  std::shared_ptr<EventWriter> eventWriter;

  std::map<std::string, float> weightsAfterCuts;

  int currentIndex;
};

#endif /* CutFlowManager_hpp */
