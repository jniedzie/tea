//  EventWriter.hpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#ifndef EventWriter_hpp
#define EventWriter_hpp

#include "ConfigManager.hpp"
#include "Event.hpp"
#include "EventReader.hpp"
#include "Helpers.hpp"

class EventWriter {
 public:
  EventWriter(const std::shared_ptr<EventReader> &eventReader_);
  ~EventWriter();

  void AddCurrentEvent(std::string treeName);

  // With HepMC events, you can specify which particles to keep.
  void AddCurrentHepMCevent(std::string treeName, const std::vector<int> &keepIndices);

  void Save();

 private:
  struct AddedBranch {
    std::string type;
    std::string collection;
    std::string variable;
    std::string sizeBranch;
    bool hasVarexp = false;
    bool IsEventLevel() const { return collection == kEventLevelBranchCollection; }
  };

  TFile *outFile;
  std::string outputFilePath;
  std::map<std::string, TTree *> outputTrees;

  std::shared_ptr<EventReader> eventReader;

  std::vector<std::string> branchesToKeep;
  std::vector<std::string> branchesToRemove;

  std::map<std::string, std::vector<bool>> boolVectorBuffers;
  std::map<std::string, std::vector<std::string>> boolVectorBranchesPerTree;

  // std::map is node-based so the addresses handed to ROOT via TTree::Branch stay valid as more
  // entries are inserted.
  std::map<std::string, AddedBranch> addedBranches;
  std::map<std::string, std::vector<std::string>> addedBranchesPerTree;
  std::map<std::string, size_t> addedVectorSizes;
  std::map<std::string, bool> everSetByApp;

  const std::vector<int> *currentKeepIndices = nullptr;

  std::map<std::string, Float_t> addedScalarFloat;
  std::map<std::string, Double_t> addedScalarDouble;
  std::map<std::string, Int_t> addedScalarInt;
  std::map<std::string, UInt_t> addedScalarUInt;
  std::map<std::string, Bool_t> addedScalarBool;
  std::map<std::string, ULong64_t> addedScalarULong;
  std::map<std::string, UChar_t> addedScalarUChar;
  std::map<std::string, Short_t> addedScalarShort;
  std::map<std::string, UShort_t> addedScalarUShort;

  std::map<std::string, Float_t[maxCollectionElements]> addedVectorFloat;
  std::map<std::string, Double_t[maxCollectionElements]> addedVectorDouble;
  std::map<std::string, Int_t[maxCollectionElements]> addedVectorInt;
  std::map<std::string, UInt_t[maxCollectionElements]> addedVectorUInt;
  std::map<std::string, Bool_t[maxCollectionElements]> addedVectorBool;
  std::map<std::string, ULong64_t[maxCollectionElements]> addedVectorULong;
  std::map<std::string, UChar_t[maxCollectionElements]> addedVectorUChar;
  std::map<std::string, Short_t[maxCollectionElements]> addedVectorShort;
  std::map<std::string, UShort_t[maxCollectionElements]> addedVectorUShort;

  std::map<std::string, std::vector<Float_t>> addedStdVectorFloat;
  std::map<std::string, std::vector<Double_t>> addedStdVectorDouble;
  std::map<std::string, std::vector<Int_t>> addedStdVectorInt;
  std::map<std::string, std::vector<UInt_t>> addedStdVectorUInt;

  void SetupOutputTree();
  void SetupBoolVectorBranches(std::string treeName);
  void RepackBoolVectorBranches(std::string treeName);

  void SetupAddedBranches(std::string treeName);
  void FillAddedBranches(std::string treeName);

  friend class CutFlowManager;
};

#endif /* EventWriter_hpp */
