//  ConfigManager.hpp
//
//  Created by Jeremi Niedziela on 09/08/2023.

#ifndef ConfigManager_hpp
#define ConfigManager_hpp

#include <Python.h>

#include "Helpers.hpp"

class ConfigManager {
 public:
  static ConfigManager& GetInstance(){ return getInstanceImpl(); }
  static void Initialize(std::string _configPath) { getInstanceImpl(&_configPath); }

  ConfigManager(ConfigManager const&) = delete;
  void operator=(ConfigManager const&) = delete;

  template <typename T>
  void GetValue(std::string name, T &outputValue);

  template <typename T>
  void GetVector(std::string name, std::vector<T> &outputVector);

  template <typename T, typename U>
  void GetMap(std::string name, std::map<T, U> &outputMap);

  void GetExtraEventCollections(std::map<std::string, ExtraCollection> &extraEventCollections);
  void GetHistogramsParams(std::map<std::string, HistogramParams> &histogramsParams, std::string collectionName);
  void GetHistogramsParams(std::map<std::string, HistogramParams2D> &histogramsParams, std::string collectionName);
  void GetHistogramsParams(std::map<std::string, IrregularHistogramParams> &histogramsParams, std::string collectionName);

  void GetScaleFactors(std::string name, std::map<std::string, ScaleFactorsMap> &scaleFactors);
  void GetScaleFactors(std::string name, std::map<std::string, ScaleFactorsTuple> &scaleFactors);

  void GetCuts(std::vector<std::pair<std::string, std::pair<float, float>>> &cuts);

  void SetInputPath(std::string path) { inputPath = path; }
  void SetTreesOutputPath(std::string path) { treesOutputPath = path; }
  void SetHistogramsOutputPath(std::string path) { histogramsOutputPath = path; }
  
 private:
  std::string configPath;
  ConfigManager(std::string* const _configPath);
  ~ConfigManager();

  static ConfigManager& getInstanceImpl(std::string* const _configPath = nullptr);

  FILE *pythonFile;
  PyObject *pythonModule;
  PyObject *config;

  PyObject *GetPythonValue(std::string name);
  PyObject *GetPythonList(std::string name);
  PyObject *GetPythonDict(std::string name);

  int GetCollectionSize(PyObject *collection);
  PyObject *GetItem(PyObject *collection, int index);

  std::string inputPath = "";
  std::string treesOutputPath = "";
  std::string histogramsOutputPath = "";
  std::string redirector = "";
};

#endif /* ConfigManager_hpp */
