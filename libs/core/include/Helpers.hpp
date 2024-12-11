#ifndef Helpers_hpp
#define Helpers_hpp

#pragma clang diagnostic push                       // save the current state
#pragma clang diagnostic ignored "-Wdocumentation"  // turn off ROOT's warnings
#pragma clang diagnostic ignored "-Wconversion"

#include <TKey.h>

#include "Math/GenVector/LorentzVector.h"
#include "Math/GenVector/PxPyPzE4D.h"
#include "TBranchElement.h"
#include "TCanvas.h"
#include "TEnv.h"
#include "TF1.h"
#include "TFile.h"
#include "TGraph.h"
#include "TGraphAsymmErrors.h"
#include "TGraphPolar.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TLatex.h"
#include "TLeaf.h"
#include "TLegend.h"
#include "TLine.h"
#include "TLorentzVector.h"
#include "TStyle.h"
#include "TTree.h"
#include "TEllipse.h"
#include "TBox.h"
#include "TMath.h"
#include "TPolyLine.h"
#include "TROOT.h"
#include "TSystem.h"
#include "TVector2.h"
#include "TRandom.h"
#include "TMatrixD.h"
#include "TVectorD.h"
#include "TRotation.h"
#include "TView3D.h"
#include "TView.h"
#include "TPolyLine3D.h"
#include "TApplication.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoVolume.h"
#include "TGeoTube.h"
#include "TGeoSphere.h"
#include "TEveManager.h"
#include "TEveGeoNode.h"
#include "TEveLine.h"
#include "TEveViewer.h"
#include "TEveProjectionManager.h"
#include "TEveProjectionAxes.h"
#include "TGLViewer.h"
#include "TGeoTorus.h"

#pragma clang diagnostic pop  // restores the saved state for diagnostics

#include <any>
#include <filesystem>
#include <iostream>
#include <random>
#include <regex>
#include <sstream>
#include <string>
#include <fstream>
#include <set>
#include <optional>

#include "Logger.hpp"

const int maxCollectionElements = 9999;
const int maxNdaughters = 5;  // Number of daughters that will be considered for HEP MC particles.
                              // Heavily affects computing time. Max is 100.

inline std::vector<std::string> getListOfTrees(TFile *file) {
  auto keys = file->GetListOfKeys();
  std::vector<std::string> trees;

  for (auto i : *keys) {
    auto key = (TKey *)i;
    if (strcmp(key->GetClassName(), "TTree") == 0) trees.push_back(key->GetName());
  }
  return trees;
}

inline std::vector<std::string> split(std::string input, char splitBy) {
  std::vector<std::string> parts;

  std::istringstream iss(input);
  std::string part;

  while (std::getline(iss, part, splitBy)) parts.push_back(part);
  return parts;
}

inline int randInt(int min, int max) {
  std::random_device rd;   // Seed generator
  std::mt19937 gen(rd());  // Mersenne Twister engine
  std::uniform_int_distribution<int> dist(min, max);
  return dist(gen);
}

inline bool inRange(float value, std::pair<float, float> range) { return value >= range.first && value <= range.second; }

inline void makeParentDirectories(std::string filePath) {
  std::filesystem::path directoryPath = std::filesystem::path(filePath).parent_path();

  if (!std::filesystem::exists(directoryPath)) {
    if (std::filesystem::create_directories(directoryPath)) {
      info() << "Created directory: " << directoryPath << std::endl;
    } else {
      error() << "Failed to create directory: " << directoryPath << std::endl;
    }
  }
}

inline bool FileExists(const std::string& name) {
  std::ifstream f(name.c_str());
  return f.good();
}

struct ExtraCollection {
  std::vector<std::string> inputCollections;
  std::map<std::string, std::pair<float, float>> allCuts;
  std::map<std::string, int> flags;
  
  void Print() {
    info() << "Input collections: " << std::endl;
    for (std::string name : inputCollections) info() << name << std::endl;

    info() << "All cuts: " << std::endl;
    for (auto &[name, cuts] : allCuts) {
      info() << "\t" << name << ": " << cuts.first << ", " << cuts.second << std::endl;
    }
    info() << "Flags: " << std::endl;
    for (auto &[name, flag] : flags) {
      info() << "\t" << name << ": " << flag << std::endl;
    }
  }
};

typedef std::map<std::tuple<float, float>, std::map<std::tuple<float, float>, std::map<std::string, float>>> ScaleFactorsMap;
typedef std::tuple<std::string, std::vector<float>> ScaleFactorsTuple;

struct HistogramParams {
  std::string collection, variable, directory;
  int nBins;
  float min, max;
  void Print() { 
    info() << "Histogram: " << directory << "/" << collection << "/" << variable;
    info() << "(" << nBins << ", " << min << ", " << max << ")" << std::endl; 
  }
};

struct IrregularHistogramParams {
  std::string collection, variable, directory;
  std::vector<float> binEdges;
};

struct HistogramParams2D {
  std::string variable, directory;
  int nBinsX, nBinsY;
  float minX, maxX, minY, maxY;
  void Print() { 
    info() << "Histogram: " << directory << "/" << variable; 
    info() << "(" << nBinsX << ", " << minX << ", " << maxX;
    info() << "," << nBinsY << ", " << minY << ", " << maxY << ")" << std::endl;
  }
};

template <class T>
double duration(T t0, T t1) {
  auto elapsed_secs = t1 - t0;
  typedef std::chrono::duration<float> float_seconds;
  auto secs = std::chrono::duration_cast<float_seconds>(elapsed_secs);
  return secs.count();
}

/// Returns current time
inline std::chrono::time_point<std::chrono::steady_clock> now() { return std::chrono::steady_clock::now(); }

#endif /* Helpers_hpp */