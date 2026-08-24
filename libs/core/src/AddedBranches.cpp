//  AddedBranches.cpp

#include "AddedBranches.hpp"

#include <algorithm>
#include <limits>

#include "ConfigManager.hpp"
#include "TTreeFormula.h"

using namespace std;

namespace {
int GetExpectedMultiplicity(const AddedBranchParams &spec) {
  return spec.IsEventLevel() ? 0 : 1;
}

template <typename T>
void CheckRange(double value, const string &type, const string &branchName) {
  auto lo = static_cast<double>(numeric_limits<T>::lowest());
  auto hi = static_cast<double>(numeric_limits<T>::max());
  if (value < lo || value > hi) {
    fatal() << "branchesToAdd: varexp value " << value << " for branch \"" << branchName
            << "\" overflows declared type " << type << " (valid range [" << lo << ", " << hi << "])" << endl;
    exit(1);
  }
}

void ValidateIntegralRange(double value, const string &type, const string &branchName) {
  if (type == "Bool_t") {
    CheckRange<Bool_t>(value, type, branchName);
  } else if (type == "UChar_t") {
    CheckRange<UChar_t>(value, type, branchName);
  } else if (type == "Short_t") {
    CheckRange<Short_t>(value, type, branchName);
  } else if (type == "UShort_t") {
    CheckRange<UShort_t>(value, type, branchName);
  } else if (type == "UInt_t") {
    CheckRange<UInt_t>(value, type, branchName);
  } else if (type == "Int_t") {
    CheckRange<Int_t>(value, type, branchName);
  }
}

template <typename Target>
void SetFormulaValue(Target &target, const string &name, const string &type, TTreeFormula *formula, int instance) {
  if (type == "Float_t") {
    target.template Set<Float_t>(name, static_cast<Float_t>(formula->EvalInstance(instance)));
  } else if (type == "Double_t") {
    target.template Set<Double_t>(name, formula->EvalInstance(instance));
  } else {
    Long64_t raw = formula->EvalInstance64(instance);
    ValidateIntegralRange(static_cast<double>(raw), type, name);
    if (type == "Int_t") {
      target.template Set<Int_t>(name, static_cast<Int_t>(raw));
    } else if (type == "UInt_t") {
      target.template Set<UInt_t>(name, static_cast<UInt_t>(raw));
    } else if (type == "Bool_t") {
      target.template Set<Bool_t>(name, raw != 0);
    } else if (type == "ULong64_t") {
      target.template Set<ULong64_t>(name, static_cast<ULong64_t>(raw));
    } else if (type == "UChar_t") {
      target.template Set<UChar_t>(name, static_cast<UChar_t>(raw));
    } else if (type == "Short_t") {
      target.template Set<Short_t>(name, static_cast<Short_t>(raw));
    } else if (type == "UShort_t") {
      target.template Set<UShort_t>(name, static_cast<UShort_t>(raw));
    }
  }
}
}  // namespace

AddedBranches::AddedBranches() {
  auto &config = ConfigManager::GetInstance();
  try {
    config.GetAddedBranchesParams(specs);
  } catch (const Exception &e) { specs = {}; }
}

AddedBranches::~AddedBranches() {
  for (auto &[name, formula] : formulas) { delete formula; }
}

void AddedBranches::Setup(const vector<string> &eventsTreeNames, const map<string, TTree *> &inputTrees) {
  static int formulaCounter = 0;

  for (auto &spec : specs) {
    bool isVectorType = kAddedVectorBranchElementTypes.count(spec.type) > 0;
    if (!isVectorType && kAddedBranchTypeCodes.find(spec.type) == kAddedBranchTypeCodes.end()) {
      fatal() << "branchesToAdd: unsupported type \"" << spec.type << "\" for branch \"" << spec.BranchName() << "\""
              << endl;
      exit(1);
    }
    if (isVectorType) {
      if (!spec.IsEventLevel()) {
        fatal() << "branchesToAdd: vector branch \"" << spec.BranchName() << "\" declares a collection (\""
                << spec.collection << "\"); vector branches are event-level only" << endl;
        exit(1);
      }
      if (!spec.varexp.empty()) {
        fatal() << "branchesToAdd: vector branch \"" << spec.BranchName()
                << "\" declares a varexp; vector branches don't support varexp yet, declare with an "
                   "empty varexp and call Event::SetVector<T>"
                << endl;
        exit(1);
      }
      continue;
    }
    if (spec.varexp.empty()) { continue; }

    string formulaName = "AddedBranches_" + spec.BranchName() + "_" + to_string(formulaCounter++);
    TTreeFormula *formula = nullptr;

    for (auto &eventsTreeName : eventsTreeNames) {
      auto *candidate = new TTreeFormula(formulaName.c_str(), spec.varexp.c_str(), inputTrees.at(eventsTreeName));
      if (candidate->GetNdim() == 0) {
        delete candidate;
        continue;
      }
      formula = candidate;
      break;
    }

    if (!formula) {
      fatal() << "branchesToAdd: varexp \"" << spec.varexp << "\" for branch \"" << spec.BranchName()
              << "\" does not compile against any events tree" << endl;
      exit(1);
    }

    int expectedMultiplicity = GetExpectedMultiplicity(spec);
    if (formula->GetMultiplicity() != expectedMultiplicity) {
      fatal() << "branchesToAdd: varexp \"" << spec.varexp << "\" for branch \"" << spec.BranchName()
              << "\" has multiplicity " << formula->GetMultiplicity() << ", expected " << expectedMultiplicity
              << " for a " << (expectedMultiplicity == 0 ? "scalar" : "per-object") << " branch" << endl;
      exit(1);
    }

    formula->SetQuickLoad(true);
    formulas[spec.BranchName()] = formula;
  }
}

void AddedBranches::Evaluate(const shared_ptr<Event> &event) {
  for (auto &spec : specs) {
    if (spec.varexp.empty()) { continue; }

    auto *formula = formulas.at(spec.BranchName());
    if (spec.IsEventLevel()) {
      EvaluateScalar(spec, formula, event);
    } else {
      EvaluateArray(spec, formula, event);
    }
  }
}

void AddedBranches::EvaluateScalar(const AddedBranchParams &spec, TTreeFormula *formula,
                                   const shared_ptr<Event> &event) {
  formula->GetNdata();
  SetFormulaValue(*event, spec.name, spec.type, formula, 0);
}

void AddedBranches::EvaluateArray(const AddedBranchParams &spec, TTreeFormula *formula,
                                  const shared_ptr<Event> &event) {
  auto collection = event->GetCollection(spec.collection);

  int nData = formula->GetNdata();
  if (nData < 0 || static_cast<size_t>(nData) != collection->size()) {
    fatal() << "branchesToAdd: varexp \"" << spec.varexp << "\" for branch \"" << spec.BranchName() << "\" produced "
            << nData << " values but collection \"" << spec.collection << "\" has " << collection->size()
            << " objects this event" << endl;
    exit(1);
  }

  size_t nObjects = min(collection->size(), static_cast<size_t>(maxCollectionElements));
  for (size_t i = 0; i < nObjects; ++i) {
    SetFormulaValue(*collection->at(i), spec.name, spec.type, formula, static_cast<int>(i));
  }
}
