//  HistogramsHandler.hpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#ifndef HistogramsHandler_hpp
#define HistogramsHandler_hpp

#include "Event.hpp"
#include "Helpers.hpp"

typedef std::pair<std::string, std::string> HistNames;

class HistogramsHandler {
 public:
  HistogramsHandler();
  ~HistogramsHandler();

  void SetEventWeights(std::map<std::string, float> weights);

  void Fill(std::string name, double value);
  void Fill(std::string name, double x, double y);
  void Fill(std::string name, double x, double y, double zOrProfileValue);
  void FillUnweighted(std::string name, double value);

  void SetHistogram1D(HistNames names, TH1D *histogram) { histograms1D[names] = histogram; }
  TH1D *GetHistogram1D(HistNames names) { return histograms1D[names]; }
  std::map<HistNames, TH1D *> GetHistograms1D() { return histograms1D; }
  std::map<HistNames, TH2D *> GetHistograms2D() { return histograms2D; }
  TH3D *GetHistogram3D(HistNames names) { return histograms3D[names]; }
  std::map<HistNames, TH3D *> GetHistograms3D() { return histograms3D; }
  TProfile2D *GetProfile2D(HistNames names) { return profiles2D[names]; }
  std::map<HistNames, TProfile2D *> GetProfiles2D() { return profiles2D; }
  void SetHistogramLabels(std::string name, std::map<int, std::string> labels);
  void SaveHistograms();
  void Print();

 private:
  std::map<HistNames, TH1D *> histograms1D;
  std::map<HistNames, TH2D *> histograms2D;
  std::map<HistNames, TH3D *> histograms3D;
  std::map<HistNames, TProfile2D *> profiles2D;
  std::map<std::string, std::string> histogramDirectories;
  std::vector<std::string> unfilledHistograms;

  std::map<std::string, HistogramParams> histParams;
  std::map<std::string, IrregularHistogramParams> irregularHistParams;
  std::map<std::string, HistogramParams2D> histParams2D;
  std::map<std::string, IrregularHistogramParams2D> irregularHistParams2D;
  std::map<std::string, HistogramParams3D> histParams3D;
  std::map<std::string, IrregularHistogramParams3D> irregularHistParams3D;
  std::map<std::string, Profile2DParams> profile2DParams;
  std::map<std::string, IrregularProfile2DParams> irregularProfile2DParams;
  std::vector<std::string> SFvariationVariables;
  std::string outputPath;
  std::map<std::string, float> eventWeights;
  bool sfSetup = false;

  void RemoveFromUnfilled(std::string name);
  void SetupHistograms();
  void SetupSFvariationHistograms();

  template <typename THist>
  THist *FindHistogram(const std::map<HistNames, THist *> &histograms, HistNames names, const char *kind);

  template <typename THist, typename... Values>
  void FillWeighted(std::map<HistNames, THist *> &histograms, const char *kind, const std::string &name,
                    Values... values);

  template <typename THist>
  void SetupVariations(std::map<HistNames, THist *> &histograms);

  template <typename THist>
  void SaveHistogram(HistNames name, THist *hist, TFile *outputFile);
};

#endif /* HistogramsHandler_hpp */
