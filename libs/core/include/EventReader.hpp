//  EventReader.hpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#ifndef EventReader_hpp
#define EventReader_hpp

#include "Event.hpp"
#include "Helpers.hpp"
#include "ConfigManager.hpp"

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

  void SetupBranches(std::string inputPath);

  void SetupScalarBranch(std::string branchName, std::string branchType);
  void SetupVectorBranch(std::string branchName, std::string branchType);
  void InitializeCollection(std::string collectionName);

  std::vector<std::string> sizeWarningsPrinted;

  std::string eventsTreeName;
  std::map<std::string, std::string> specialBranchSizes;
  std::map<std::string, bool> isCollectionAnStdVector;
  std::map<std::string, std::string> branchNamesAndTypes;

  template <typename First, typename... Rest>
  int tryGet(std::shared_ptr<Event> event, std::string branchName);

  friend class EventWriter;
  friend class CutFlowManager;
};

#endif /* EventReader_hpp */
