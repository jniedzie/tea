//  EventWriter.hpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#ifndef EventWriter_hpp
#define EventWriter_hpp

#include "Event.hpp"
#include "EventReader.hpp"
#include "Helpers.hpp"
#include "ConfigManager.hpp"

class EventWriter {
public:
  EventWriter(std::string configPath,
              const std::shared_ptr<EventReader> &eventReader_);
  ~EventWriter();

  void AddCurrentEvent(std::string treeName);
  void Save();

private:
  std::unique_ptr<ConfigManager> config;

  TFile *outFile;
  std::map<std::string, TTree *> outputTrees;

  std::shared_ptr<EventReader> eventReader;

  void SetupOutputTree(std::string outFileName);

  friend class CutFlowManager;
};

#endif /* EventWriter_hpp */
