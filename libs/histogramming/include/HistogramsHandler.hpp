//  HistogramsHandler.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef HistogramsHandler_hpp
#define HistogramsHandler_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class HistogramsHandler {
 public:
  HistogramsHandler();
  ~HistogramsHandler();

  void SetEventWeights(std::map<std::string,float> weights);

  void Fill(std::string name, double value);
  void Fill(std::string name, double valueX, double valueY);

  void SetHistogram1D(std::tuple<std::string,std::string> names, TH1D *histogram) { histograms1D[names] = histogram; }
  TH1D* GetHistogram1D(std::tuple<std::string,std::string> names) { return histograms1D[names]; }
  std::map<std::tuple<std::string,std::string>, TH1D*> GetHistograms1D() { return histograms1D; }
  void SaveHistograms();
  
 private:
  std::map<std::tuple<std::string,std::string>, TH1D*> histograms1D;
  std::map<std::tuple<std::string,std::string>, TH2D*> histograms2D;

  std::map<std::string, HistogramParams> histParams;
  std::map<std::string, IrregularHistogramParams> irregularHistParams;
  std::map<std::string, HistogramParams2D> histParams2D;
  std::vector<std::string> SFvariationVariables;
  std::string outputPath;
  std::map<std::string,float> eventWeights;
  std::vector<std::string> extraSFs;

  void CheckHistogram(std::string name, std::string directory);
  void SetupHistograms();
  void SetupSFvariationHistograms();

  template <typename THist>
  void SaveHistogram(std::tuple<std::string,std::string> name, THist* hist, TFile* outputFile);
};

#endif /* HistogramsHandler_hpp */
