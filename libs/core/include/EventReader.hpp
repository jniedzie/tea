//  EventReader.hpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#ifndef EventReader_hpp
#define EventReader_hpp

#include "ConfigManager.hpp"
#include "Event.hpp"
#include "Helpers.hpp"

class EventReader {
 public:
  EventReader();
  ~EventReader();

  long long GetNevents() const;
  std::shared_ptr<Event> GetEvent(int iEvent);

 private:
  int maxEvents;
  int printEveryNevents;

  TFile *inputFile;
  std::map<std::string, TTree *> inputTrees;
  std::shared_ptr<Event> currentEvent;

  std::tuple<std::string, std::string> GetCollectionAndVariableNames(std::string branchName);

  void SetupTrees();
  void SetupBranches();

  void SetupScalarBranch(std::string branchName, std::string branchType, std::string eventsTreeName);
  void SetupVectorBranch(std::string branchName, std::string branchType, std::string eventsTreeName);
  void InitializeCollection(std::string collectionName);

  std::vector<std::string> sizeWarningsPrinted;

  std::vector<std::string> eventsTreeNames;
  std::map<std::string, std::string> specialBranchSizes;
  std::map<std::string, bool> isCollectionAnStdVector;
  std::map<std::string, std::string> branchNamesAndTypes;

  TLeaf *GetLeaf(TBranch *branch);

  template <typename First, typename... Rest>
  int tryGet(std::shared_ptr<Event> event, std::string branchName);

  friend class EventWriter;
  friend class CutFlowManager;
};

#endif /* EventReader_hpp */
