//  ConfigManager.hpp
//
//  Created by Jeremi Niedziela on 09/08/2023.

#ifndef ConfigManager_hpp
#define ConfigManager_hpp

#include <Python.h>

#include "Helpers.hpp"

class ConfigManager {
 public:
  ConfigManager(std::string configPath);
  ~ConfigManager();

  template <typename T>
  void GetValue(std::string name, T &outputValue);

  template <typename T>
  void GetVector(std::string name, std::vector<T> &outputVector);

  template <typename T, typename U>
  void GetMap(std::string name, std::map<T, U> &outputMap);

  void GetExtraEventCollections(std::map<std::string, ExtraCollection> &extraEventCollections);

  void GetSelections(std::map<std::string, std::pair<float, float>> &selections);

 private:
  FILE *pythonFile;
  PyObject *pythonModule;
  PyObject *config;

  PyObject *GetPythonValue(std::string name);
  PyObject *GetPythonList(std::string name);
  PyObject *GetPythonDict(std::string name);

  int GetCollectionSize(PyObject *collection);
  PyObject *GetItem(PyObject *collection, int index);
};

#endif /* ConfigManager_hpp */
