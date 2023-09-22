//  HistogramsHandler.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef HistogramsHandler_hpp
#define HistogramsHandler_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class HistogramsHandler {
 public:
  HistogramsHandler(std::string configPath);
  ~HistogramsHandler();

  void CheckHistogram(std::string name){
    if (!histograms1D.count(name)) error() << "Couldn't find key: " << name << " in histograms map\n";
  }

  void SetupHistograms();
  void SaveHistograms();

  std::map<std::string, TH1D*> histograms1D;
  std::map<std::string, TH2D*> histograms2D;

 private:
  std::map<std::string, std::string> histTitles;
  std::map<std::string, int> histNbins;
  std::map<std::string, float> histMin;
  std::map<std::string, float> histMax;
  std::map<std::string, std::string> histOutputDir;

  std::string outputPath;
};

#endif /* HistogramsHandler_hpp */
