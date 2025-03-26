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

  void SetEventWeights(std::map<std::string,float> weights) { eventWeights = weights; };

  void Fill(std::string name, double value);
  void Fill(std::string name, double valueX, double valueY);

  void SetHistogram1D(std::string name, TH1D *histogram) { histograms1D[name] = histogram; }
  TH1D* GetHistogram1D(std::string name) { return histograms1D[name]; }
  std::map<std::string, TH1D*> GetHistograms1D() { return histograms1D; }
  void SaveHistograms();

 private:
  std::map<std::string, TH1D*> histograms1D;
  std::map<std::string, TH2D*> histograms2D;

  std::map<std::string, HistogramParams> histParams;
  std::map<std::string, IrregularHistogramParams> irregularHistParams;
  std::map<std::string, HistogramParams2D> histParams2D;
  std::string outputPath;
  std::map<std::string,float> eventWeights;
  std::vector<std::string> scaleFactorTypes;

  void CheckHistogram(std::string name);
  void SetupHistograms();
};

#endif /* HistogramsHandler_hpp */
