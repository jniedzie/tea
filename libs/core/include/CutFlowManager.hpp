//  CutFlowManager.hpp
//
//  Created by Jeremi Niedziela on 16/08/2023.

#ifndef CutFlowManager_hpp
#define CutFlowManager_hpp

#include "EventReader.hpp"
#include "EventWriter.hpp"
#include "Helpers.hpp"

class CutFlowManager {
 public:
  CutFlowManager(std::shared_ptr<EventReader> eventReader_, std::shared_ptr<EventWriter> eventWriter_ = nullptr);
  ~CutFlowManager();

  void RegisterCut(std::string cutName);
  void UpdateCutFlow(std::string cutName);
  bool HasCut(std::string cutName);
  void SaveCutFlow();
  std::map<std::string, float> GetCutFlow();
  void Print();

  bool isEmpty() { return weightsAfterCuts.empty(); }

 private:
  std::string weightsBranchName;

  std::shared_ptr<EventReader> eventReader;
  std::shared_ptr<EventWriter> eventWriter;

  std::map<std::string, float> weightsAfterCuts;

  int currentIndex;
  bool inputContainsInitial;

  std::vector<std::string> existingCuts;
  bool weightsBranchWarningPrinted = false;

  float GetCurrentEventWeight();
  std::string GetFullCutName(std::string cutName);
};

#endif /* CutFlowManager_hpp */
