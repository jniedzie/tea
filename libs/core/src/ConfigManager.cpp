//  ConfigManager.cpp
//
//  Created by Jeremi Niedziela on 09/08/2023.

#include "ConfigManager.hpp"

#include <type_traits>

#include "Logger.hpp"

using namespace std;

ConfigManager::ConfigManager(std::string *const _configPath) : configPath(move(*_configPath)) {
  if (nullptr == _configPath) throw std::runtime_error{"ConfigManager not initialized"};

  Py_Initialize();

  pythonFile = fopen(configPath.c_str(), "r");

  if (!pythonFile) {
    fatal() << "Could not parse python config" << endl;
    Py_Finalize();
    exit(1);
  }

  PyRun_SimpleFile(pythonFile, configPath.c_str());
  fclose(pythonFile);

  pythonModule = PyImport_ImportModule("__main__");
  if (!pythonModule) {
    fatal() << "Couldn't import __main__ from the python module" << endl;
    Py_Finalize();
    exit(1);
  }

  config = PyModule_GetDict(pythonModule);
}

ConfigManager::~ConfigManager() { Py_Finalize(); }

int ConfigManager::GetCollectionSize(PyObject *collection) {
  int size = -1;
  if (PyList_Check(collection))
    size = PyList_Size(collection);
  else if (PyTuple_Check(collection))
    size = PyTuple_Size(collection);
  return size;
}

PyObject *ConfigManager::GetItem(PyObject *collection, int index) {
  PyObject *item;

  if (PyList_Check(collection))
    item = PyList_GetItem(collection, index);
  else if (PyTuple_Check(collection))
    item = PyTuple_GetItem(collection, index);

  return item;
}

//-------------------------------------------------------------------------------------------------
// Methods to retrieve a value/list/dict from the python file
//-------------------------------------------------------------------------------------------------

PyObject *ConfigManager::GetPythonValue(string name) {
  PyObject *pythonValue = PyDict_GetItemString(config, name.c_str());
  if (!pythonValue) {
    throw Exception(("Could not find a value in python config file: " + name).c_str());
  }
  return pythonValue;
}

PyObject *ConfigManager::GetPythonList(string name) {
  PyObject *pythonList = PyDict_GetItemString(config, name.c_str());

  if (!pythonList || (!PyList_Check(pythonList) && !PyTuple_Check(pythonList))) {
    throw Exception(("Could not find a list/tuple in python config file: " + name).c_str());
  }
  return pythonList;
}

PyObject *ConfigManager::GetPythonDict(string name) {
  PyObject *pythonDict = PyDict_GetItemString(config, name.c_str());
  if (!pythonDict || !PyDict_Check(pythonDict)) {
    throw Exception(("Could not find a dict in python config file: " + name).c_str());
  }
  return pythonDict;
}

//-------------------------------------------------------------------------------------------------
// Template specializations to extract a value from the python file
//-------------------------------------------------------------------------------------------------

template <>
void ConfigManager::GetValue<string>(std::string name, string &outputValue) {
  if (name == "inputFilePath" && inputPath != "") {
    outputValue = inputPath;
    return;
  }
  if ((name == "treeOutputFilePath" || name == "histogramsOutputFilePath") && outputPath != "") {
    outputValue = outputPath;
    return;
  }

  PyObject *pythonValue = GetPythonValue(name);
  if (!pythonValue || !PyUnicode_Check(pythonValue)) {
    error() << "Failed retriving python value (string)" << endl;
    return;
  }
  outputValue = PyUnicode_AsUTF8(pythonValue);
}

template <>
void ConfigManager::GetValue<int>(std::string name, int &outputValue) {
  PyObject *pythonValue = GetPythonValue(name);
  if (!pythonValue || (!PyUnicode_Check(pythonValue) && !PyLong_Check(pythonValue))) {
    error() << "Failed retriving python value (int)" << endl;
    return;
  }
  outputValue = PyLong_AsLong(pythonValue);
}

template <>
void ConfigManager::GetValue<bool>(std::string name, bool &outputValue) {
  PyObject *pythonValue = GetPythonValue(name);
  if (!pythonValue || (!PyUnicode_Check(pythonValue) && !PyBool_Check(pythonValue))) {
    error() << "Failed retriving python value (int)" << endl;
    return;
  }
  outputValue = PyLong_AsLong(pythonValue);
}

template <>
void ConfigManager::GetValue<float>(std::string name, float &outputValue) {
  PyObject *pythonValue = GetPythonValue(name);
  if (!pythonValue || !PyFloat_Check(pythonValue)) {
    error() << "Failed retriving python value (float)" << endl;
    return;
  }
  outputValue = PyFloat_AsDouble(pythonValue);
}

//-------------------------------------------------------------------------------------------------
// Template specializations to extract a vector from the python file
//-------------------------------------------------------------------------------------------------

template <>
void ConfigManager::GetVector<std::string>(std::string name, std::vector<std::string> &outputVector) {
  PyObject *pythonList = GetPythonList(name);

  for (Py_ssize_t i = 0; i < GetCollectionSize(pythonList); ++i) {
    PyObject *item = GetItem(pythonList, i);

    if (!item || !PyUnicode_Check(item)) {
      error() << "Failed retriving python vector<string>" << endl;
      continue;
    }
    std::string value = PyUnicode_AsUTF8(item);
    outputVector.push_back(value);
  }
}

//-------------------------------------------------------------------------------------------------
// Template specializations to extract a map from the python file
//-------------------------------------------------------------------------------------------------

template <>
void ConfigManager::GetMap<std::string, std::string>(std::string name, std::map<std::string, std::string> &outputMap) {
  PyObject *pythonDict = GetPythonDict(name);

  PyObject *pKey, *pValue;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &pKey, &pValue)) {
    if (!PyUnicode_Check(pKey) || !PyUnicode_Check(pValue)) {
      error() << "Failed retriving python key-value pair (string-string)" << endl;
      continue;
    }
    outputMap[PyUnicode_AsUTF8(pKey)] = PyUnicode_AsUTF8(pValue);
  }
}

template <>
void ConfigManager::GetMap<std::string, int>(std::string name, std::map<std::string, int> &outputMap) {
  PyObject *pythonDict = GetPythonDict(name);

  PyObject *pKey, *pValue;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &pKey, &pValue)) {
    if (!PyUnicode_Check(pKey) || !PyLong_Check(pValue)) {
      error() << "Failed retriving python key-value pair (string-int)" << endl;
      continue;
    }
    outputMap[PyUnicode_AsUTF8(pKey)] = PyLong_AsLong(pValue);
  }
}

template <>
void ConfigManager::GetMap<std::string, float>(std::string name, std::map<std::string, float> &outputMap) {
  PyObject *pythonDict = GetPythonDict(name);

  PyObject *pKey, *pValue;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &pKey, &pValue)) {
    if (!PyUnicode_Check(pKey) || (!PyFloat_Check(pValue) && !PyLong_Check(pValue))) {
      error() << "Failed retriving python key-value pair (string-float)" << endl;
      continue;
    }
    outputMap[PyUnicode_AsUTF8(pKey)] = PyFloat_AsDouble(pValue);
  }
}

template <>
void ConfigManager::GetMap<std::string, bool>(std::string name, std::map<std::string, bool> &outputMap) {
  PyObject *pythonDict = GetPythonDict(name);

  PyObject *pKey, *pValue;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &pKey, &pValue)) {
    if (!PyUnicode_Check(pKey) || !PyLong_Check(pValue)) {
      error() << "Failed retriving python key-value pair (string-bool)" << endl;
      continue;
    }
    outputMap[PyUnicode_AsUTF8(pKey)] = PyLong_AsLong(pValue);
  }
}

template <>
void ConfigManager::GetMap<string, vector<string>>(string name, map<string, vector<string>> &outputMap) {
  PyObject *pythonDict = GetPythonDict(name);

  PyObject *pKey, *pValue;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &pKey, &pValue)) {
    if (!PyUnicode_Check(pKey) || (!PyList_Check(pValue) && !PyTuple_Check(pValue))) {
      error() << "Failed retriving python key-value pair (string-vector<string>)" << endl;
      continue;
    }
    vector<string> outputVector;
    for (Py_ssize_t i = 0; i < GetCollectionSize(pValue); ++i) {
      PyObject *item = GetItem(pValue, i);
      outputVector.push_back(PyUnicode_AsUTF8(item));
    }
    outputMap[PyUnicode_AsUTF8(pKey)] = outputVector;
  }
}

template <>
void ConfigManager::GetMap<int, vector<vector<int>>>(string name, map<int, vector<vector<int>>> &outputMap) {
  PyObject *pythonDict = GetPythonDict(name);

  PyObject *pKey, *pOuterList;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &pKey, &pOuterList)) {
    if (!PyUnicode_Check(pKey) || (!PyList_Check(pOuterList) && !PyTuple_Check(pOuterList))) {
      error() << "Failed retriving python key-value pair (int-vector<vector<int>>)" << endl;
      continue;
    }
    
    vector<vector<int>> outerVector;

    for (Py_ssize_t i = 0; i < GetCollectionSize(pOuterList); ++i) {
      PyObject *pInnerList = GetItem(pOuterList, i);

      vector<int> innerVector;

      for (Py_ssize_t j = 0; j < GetCollectionSize(pInnerList); ++j) {
        PyObject *pValue = GetItem(pInnerList, j);
        innerVector.push_back(PyLong_AsLong(pValue));
      }

      outerVector.push_back(innerVector);
    }
    outputMap[stoi(PyUnicode_AsUTF8(pKey))] = outerVector;
  }
}

//-------------------------------------------------------------------------------------------------
// Other methods
//-------------------------------------------------------------------------------------------------

void ConfigManager::GetExtraEventCollections(map<string, ExtraCollection> &extraEventCollections) {
  PyObject *pythonDict = GetPythonDict("extraEventCollections");

  PyObject *collectionName, *collectionSettings;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &collectionName, &collectionSettings)) {
    if (!PyUnicode_Check(collectionName)) {
      error() << "Failed retriving python collection name (string)" << endl;
      continue;
    }
    PyObject *pyKey = nullptr;
    PyObject *pyValue = nullptr;
    Py_ssize_t pos2 = 0;
    ExtraCollection extraCollection;

    while (PyDict_Next(collectionSettings, &pos2, &pyKey, &pyValue)) {
      string keyStr = PyUnicode_AsUTF8(pyKey);
      if (keyStr == "inputCollections") {
        for (Py_ssize_t i = 0; i < GetCollectionSize(pyValue); ++i) {
          PyObject *item = GetItem(pyValue, i);
          extraCollection.inputCollections.push_back(PyUnicode_AsUTF8(item));
        }
      } else if (PyTuple_Check(pyValue)) {
        PyObject *min = GetItem(pyValue, 0);
        PyObject *max = GetItem(pyValue, 1);
        if(PyFloat_Check(min) && PyFloat_Check(max)){
          extraCollection.selections[keyStr] = {PyFloat_AsDouble(min), PyFloat_AsDouble(max)};
        }
        else if(PyLong_Check(min) && PyLong_Check(max)){
          extraCollection.optionRanges[keyStr] = {PyLong_AsLong(min), PyLong_AsLong(max)};
        }
        else{
          error() << "Failed retriving python tuple (float,float) or (int,int)" << endl;
        }
      } else if (PyBool_Check(pyValue)) {
        extraCollection.flags[keyStr] = PyLong_AsLong(pyValue);
      } else if (PyLong_Check(pyValue)) {
        extraCollection.options[keyStr] = PyLong_AsLong(pyValue);
      }
    }

    extraEventCollections[PyUnicode_AsUTF8(collectionName)] = extraCollection;
  }
}

void ConfigManager::GetScaleFactors(string name, map<string, ScaleFactorsMap> &scaleFactors) {
  PyObject *pythonDict = GetPythonDict(name.c_str());

  PyObject *SFname, *SFvalues;
  Py_ssize_t pos0 = 0;

  while (PyDict_Next(pythonDict, &pos0, &SFname, &SFvalues)) {
    if (!PyUnicode_Check(SFname)) {
      error() << "Failed retriving python scale factor name (string)" << endl;
      continue;
    }
    string SFnameStr = PyUnicode_AsUTF8(SFname);
    scaleFactors[SFnameStr] = ScaleFactorsMap();

    PyObject *etaBin, *valuesForEta;
    Py_ssize_t pos = 0;

    while (PyDict_Next(SFvalues, &pos, &etaBin, &valuesForEta)) {
      if (!PyTuple_Check(etaBin)) {
        error() << "Failed retriving python eta bin" << endl;
        continue;
      }
      PyObject *ptBin = nullptr;
      PyObject *values = nullptr;
      Py_ssize_t pos2 = 0;

      tuple<float, float> etaBinValues = {PyFloat_AsDouble(GetItem(etaBin, 0)), PyFloat_AsDouble(GetItem(etaBin, 1))};

      while (PyDict_Next(valuesForEta, &pos2, &ptBin, &values)) {
        tuple<float, float> ptBinValues = {PyFloat_AsDouble(GetItem(ptBin, 0)), PyFloat_AsDouble(GetItem(ptBin, 1))};

        PyObject *fieldName = nullptr;
        PyObject *fieldValue = nullptr;
        Py_ssize_t pos3 = 0;

        while (PyDict_Next(values, &pos3, &fieldName, &fieldValue)) {
          scaleFactors[SFnameStr][etaBinValues][ptBinValues][PyUnicode_AsUTF8(fieldName)] = PyFloat_AsDouble(fieldValue);
        }
      }
    }
  }
}

void ConfigManager::GetScaleFactors(string name, map<string, ScaleFactorsTuple> &scaleFactors) {
  PyObject *pythonDict = GetPythonDict(name.c_str());

  PyObject *SFname, *SFvalues;
  Py_ssize_t pos0 = 0;

  while (PyDict_Next(pythonDict, &pos0, &SFname, &SFvalues)) {
    if (!PyUnicode_Check(SFname)) {
      error() << "Failed retriving python scale factor name (string)" << endl;
      continue;
    }
    string SFnameStr = PyUnicode_AsUTF8(SFname);
    scaleFactors[SFnameStr] = ScaleFactorsTuple();

    PyObject *tupleFormula = GetItem(SFvalues, 0);
    string formulaString = PyUnicode_AsUTF8(tupleFormula);
    
    PyObject *tupleParams = GetItem(SFvalues, 1);
    
    vector<float> params;
    for (Py_ssize_t i = 0; i < GetCollectionSize(tupleParams); ++i) {
      PyObject *item = GetItem(tupleParams, i);
      params.push_back(PyFloat_AsDouble(item));
    }
    scaleFactors[SFnameStr] = {formulaString, params};    
  }
}

void ConfigManager::GetHistogramsParams(map<std::string, HistogramParams> &histogramsParams, string collectionName) {
  PyObject *pythonList = GetPythonList(collectionName);

  for (Py_ssize_t i = 0; i < GetCollectionSize(pythonList); ++i) {
    PyObject *params = GetItem(pythonList, i);

    HistogramParams histParams;
    string title;

    if (GetCollectionSize(params) == 6) {
      histParams.collection = PyUnicode_AsUTF8(GetItem(params, 0));
      histParams.variable = PyUnicode_AsUTF8(GetItem(params, 1));
      histParams.nBins = PyLong_AsLong(GetItem(params, 2));
      histParams.min = PyFloat_AsDouble(GetItem(params, 3));
      histParams.max = PyFloat_AsDouble(GetItem(params, 4));
      histParams.directory = PyUnicode_AsUTF8(GetItem(params, 5));
      title = histParams.collection + "_" + histParams.variable;
    } else {
      histParams.variable = PyUnicode_AsUTF8(GetItem(params, 0));
      histParams.nBins = PyLong_AsLong(GetItem(params, 1));
      histParams.min = PyFloat_AsDouble(GetItem(params, 2));
      histParams.max = PyFloat_AsDouble(GetItem(params, 3));
      histParams.directory = PyUnicode_AsUTF8(GetItem(params, 4));
      title = histParams.variable;
    }
    histogramsParams[title] = histParams;
  }
}

void ConfigManager::GetHistogramsParams(std::map<std::string, HistogramParams2D> &histogramsParams, string collectionName) {
  PyObject *pythonList = GetPythonList(collectionName);

  for (Py_ssize_t i = 0; i < GetCollectionSize(pythonList); ++i) {
    PyObject *params = GetItem(pythonList, i);

    HistogramParams2D histParams;

    histParams.variable = PyUnicode_AsUTF8(GetItem(params, 0));
    histParams.nBinsX = PyLong_AsLong(GetItem(params, 1));
    histParams.minX = PyFloat_AsDouble(GetItem(params, 2));
    histParams.maxX = PyFloat_AsDouble(GetItem(params, 3));
    histParams.nBinsY = PyLong_AsLong(GetItem(params, 4));
    histParams.minY = PyFloat_AsDouble(GetItem(params, 5));
    histParams.maxY = PyFloat_AsDouble(GetItem(params, 6));
    histParams.directory = PyUnicode_AsUTF8(GetItem(params, 7));

    histogramsParams[histParams.variable] = histParams;
  }
}

void ConfigManager::GetSelections(vector<pair<string, pair<float, float>>> &selections) {
  PyObject *pythonDict = GetPythonDict("eventSelections");

  PyObject *cutName, *cutValues;
  Py_ssize_t pos = 0;

  while (PyDict_Next(pythonDict, &pos, &cutName, &cutValues)) {
    if (!PyUnicode_Check(cutName)) {
      error() << "Failed retriving python cut name (string)" << endl;
      continue;
    }
    PyObject *min = GetItem(cutValues, 0);
    PyObject *max = GetItem(cutValues, 1);
    selections.push_back({PyUnicode_AsUTF8(cutName), {PyFloat_AsDouble(min), PyFloat_AsDouble(max)}});
  }
}
