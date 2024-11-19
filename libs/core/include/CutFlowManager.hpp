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

  void RegisterPreExistingCutFlows(std::string collectionName = "");
  void RegisterCollection(std::string collectionName);

  void RegisterCut(std::string cutName, std::string collectionName = "");
  void UpdateCutFlow(std::string cutName, std::string collectionName = "");
  bool HasCut(std::string cutName, std::string collectionName = "");
  void SaveCutFlow(std::string collectionName = "");
  std::map<std::string, float> GetCutFlow(std::string collectionName = "");
  void Print(std::string collectionName = "");

  bool isEmpty(std::string collectionName = "") { return weightsAfterCuts.empty(); }

  void SaveAllCutFlows();

 private:
  std::string weightsBranchName;

  std::shared_ptr<EventReader> eventReader;
  std::shared_ptr<EventWriter> eventWriter;

  std::map<std::string, float> weightsAfterCuts;
  std::map<std::string,std::map<std::string, float>> weightsAfterCollectionCuts;

  int currentIndex;
  std::map<std::string,int> currentCollectionIndex;
  bool inputContainsInitial;
  std::map<std::string,bool> inputCollectionContainsInitial;

  std::vector<std::string> existingCuts;
  std::map<std::string,std::vector<std::string>> existingCollectionCuts;
  bool weightsBranchWarningPrinted = false;

  float GetCurrentEventWeight();
  std::string GetFullCutName(std::string cutName, std::string collectionName = "");
};

#endif /* CutFlowManager_hpp */
