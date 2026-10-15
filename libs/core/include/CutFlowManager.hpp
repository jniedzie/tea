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

  void RegisterCollection(std::string collectionName);

  void RegisterCut(std::string cutName, std::string collectionName = "");
  void UpdateCutFlow(std::string cutName, std::string collectionName = "");
  bool HasCut(std::string cutName, std::string collectionName = "");
  std::map<std::string, double> GetCutFlow(std::string collectionName = "");
  std::map<std::string, double> GetRawEventsCutFlow(std::string collectionName = "");
  void Print(std::string collectionName = "");

  bool isEmpty(std::string collectionName = "");
  bool isRawEventsEmpty(std::string collectionName = "");

  void SaveCutFlow();

  // event weights (standard and up/down variations) mapped to strings naming type the of event weigth
  void SetEventWeight(double weight) { eventWeight = weight; };

 private:
  std::string weightsBranchName;

  std::shared_ptr<EventReader> eventReader;
  std::shared_ptr<EventWriter> eventWriter;

  std::map<std::string, double> weightsAfterCuts;
  std::map<std::string, double> rawEventsAfterCuts;
  std::map<std::string, std::map<std::string, double>> weightsAfterCollectionCuts;
  std::map<std::string, std::map<std::string, double>> rawEventsAfterCollectionCuts;
  double eventWeight = 0;

  int currentIndex;
  std::map<std::string, int> currentCollectionIndex;
  bool inputContainsInitial;
  std::map<std::string, bool> inputCollectionContainsInitial;

  std::vector<std::string> existingCuts;
  std::map<std::string, std::vector<std::string>> existingCollectionCuts;
  bool weightsBranchWarningPrinted = false;

  double GetCurrentEventWeight();
  std::string GetFullCutName(std::string cutName, std::string collectionName = "");
  void RegisterPreExistingCutFlows();
  void SaveSingleCutFlow(std::string collectionName = "");
  void WriteCutFlow(std::map<std::string, double> weights, std::string cutFlowName);
};

#endif /* CutFlowManager_hpp */
