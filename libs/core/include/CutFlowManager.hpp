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
  CutFlowManager(std::shared_ptr<EventReader> eventReader_, std::shared_ptr<EventWriter> eventWriter_ = nullptr, std::vector<std::string> additionalCutFlowCollections = {});
  ~CutFlowManager();

  void RegisterCut(std::string cutName);
  void UpdateCutFlow(std::string cutName);
  bool HasCut(std::string cutName);
  void SaveCutFlow();
  std::map<std::string, float> GetCutFlow();
  void Print();

  bool isEmpty() { return weightsAfterCuts.empty(); }

  void RegisterCutForCollection(std::string collectionName, std::string cutName);
  void UpdateCutFlowForCollection(std::string collectionName, std::string cutName);
  bool HasCutInCollection(std::string collectionName, std::string cutName);
  void SaveCutFlowForCollections(std::string collectionName);
  std::map<std::string, float> GetCutFlowForCollection(std::string collectionName);
  void PrintCutFlowForCollection(std::string collectionName);

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
