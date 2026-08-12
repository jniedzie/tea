//  AddedBranches.cpp

#include "AddedBranches.hpp"

#include <algorithm>

#include "ConfigManager.hpp"
#include "TTreeFormula.h"

using namespace std;

namespace {
int GetExpectedMultiplicity(const AddedBranchParams &spec) { return spec.collection.empty() ? 0 : 1; }

// TTreeFormula evaluates in double; integral targets go through EvalInstance64 instead (exact
// for a bare branch reference), but a declared narrower type (Bool_t, UChar_t, ...) can still
// silently truncate a wider value, so range-check before casting rather than truncate.
void ValidateIntegralRange(double value, const string &type, const string &branchName) {
  auto checkRange = [&](double lo, double hi) {
    if (value < lo || value > hi) {
      fatal() << "branchesToAdd: varexp value " << value << " for branch \"" << branchName << "\" overflows declared type "
              << type << " (valid range [" << lo << ", " << hi << "])" << endl;
      exit(1);
    }
  };
  if (type == "Bool_t")
    checkRange(0, 1);
  else if (type == "UChar_t")
    checkRange(0, 255);
  else if (type == "Short_t")
    checkRange(-32768, 32767);
  else if (type == "UShort_t")
    checkRange(0, 65535);
  else if (type == "UInt_t")
    checkRange(0, 4294967295.0);
  else if (type == "Int_t")
    checkRange(-2147483648.0, 2147483647.0);
  // ULong64_t already comes out of EvalInstance64 at full integer width; nothing to narrow.
}

// Target is Event or PhysicsObject -- both expose the same template<typename T> Set(name, value).
template <typename Target>
void SetFormulaValue(Target &target, const string &name, const string &type, TTreeFormula *formula, int instance) {
  if (type == "Float_t") {
    target.template Set<Float_t>(name, static_cast<Float_t>(formula->EvalInstance(instance)));
  } else if (type == "Double_t") {
    target.template Set<Double_t>(name, formula->EvalInstance(instance));
  } else {
    Long64_t raw = formula->EvalInstance64(instance);
    ValidateIntegralRange(static_cast<double>(raw), type, name);
    if (type == "Int_t")
      target.template Set<Int_t>(name, static_cast<Int_t>(raw));
    else if (type == "UInt_t")
      target.template Set<UInt_t>(name, static_cast<UInt_t>(raw));
    else if (type == "Bool_t")
      target.template Set<Bool_t>(name, raw != 0);
    else if (type == "ULong64_t")
      target.template Set<ULong64_t>(name, static_cast<ULong64_t>(raw));
    else if (type == "UChar_t")
      target.template Set<UChar_t>(name, static_cast<UChar_t>(raw));
    else if (type == "Short_t")
      target.template Set<Short_t>(name, static_cast<Short_t>(raw));
    else if (type == "UShort_t")
      target.template Set<UShort_t>(name, static_cast<UShort_t>(raw));
  }
}
}  // namespace

AddedBranches::AddedBranches() {
  auto &config = ConfigManager::GetInstance();
  try {
    config.GetAddedBranchesParams(specs);
  } catch (const Exception &e) {
    specs = {};  // no branchesToAdd key in config: nothing to add
  }
}

AddedBranches::~AddedBranches() {
  for (auto &[name, formula] : formulas) delete formula;
}

void AddedBranches::Setup(const vector<string> &eventsTreeNames, const map<string, TTree *> &inputTrees) {
  static int formulaCounter = 0;

  for (auto &spec : specs) {
    if (kAddedBranchTypeCodes.find(spec.type) == kAddedBranchTypeCodes.end()) {
      fatal() << "branchesToAdd: unsupported type \"" << spec.type << "\" for branch \"" << spec.BranchName() << "\"" << endl;
      exit(1);
    }
    if (spec.varexp.empty()) continue;  // app-set only, nothing to compile/pre-fill

    string formulaName = "AddedBranches_" + spec.BranchName() + "_" + to_string(formulaCounter++);
    TTreeFormula *formula = nullptr;

    // A varexp must be compiled against the events tree that actually holds its branches; try
    // each in turn (matters only when eventsTreeNames lists more than one tree).
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

    // Catches the wrong *class* of expression (an array varexp on an event-level branch or vice
    // versa) statically. A same-class mismatch (e.g. Jet_pt*2 declared on a Muon_ branch) still
    // has multiplicity 1 and only diverges at runtime -- see the GetNdata() check in EvaluateArray.
    int expectedMultiplicity = GetExpectedMultiplicity(spec);
    if (formula->GetMultiplicity() != expectedMultiplicity) {
      fatal() << "branchesToAdd: varexp \"" << spec.varexp << "\" for branch \"" << spec.BranchName() << "\" has multiplicity "
              << formula->GetMultiplicity() << ", expected " << expectedMultiplicity << " for a "
              << (expectedMultiplicity == 0 ? "scalar" : "per-object") << " branch" << endl;
      exit(1);
    }

    formula->SetQuickLoad(true);
    formulas[spec.BranchName()] = formula;
  }
}

void AddedBranches::Evaluate(const shared_ptr<Event> &event) {
  for (auto &spec : specs) {
    if (spec.varexp.empty()) continue;  // app-set only, no pre-fill

    auto *formula = formulas.at(spec.BranchName());
    if (spec.collection.empty())
      EvaluateScalar(spec, formula, event);
    else
      EvaluateArray(spec, formula, event);
  }
}

void AddedBranches::EvaluateScalar(const AddedBranchParams &spec, TTreeFormula *formula, const shared_ptr<Event> &event) {
  formula->GetNdata();  // refreshes the formula's cached state for the current entry
  SetFormulaValue(*event, spec.name, spec.type, formula, 0);
}

void AddedBranches::EvaluateArray(const AddedBranchParams &spec, TTreeFormula *formula, const shared_ptr<Event> &event) {
  auto collection = event->GetCollection(spec.collection);

  int nData = formula->GetNdata();
  if (nData < 0 || static_cast<size_t>(nData) != collection->size()) {
    fatal() << "branchesToAdd: varexp \"" << spec.varexp << "\" for branch \"" << spec.BranchName() << "\" produced " << nData
            << " values but collection \"" << spec.collection << "\" has " << collection->size() << " objects this event"
            << endl;
    exit(1);
  }

  size_t nObjects = min(collection->size(), static_cast<size_t>(maxCollectionElements));
  for (size_t i = 0; i < nObjects; ++i) {
    SetFormulaValue(*collection->at(i), spec.name, spec.type, formula, static_cast<int>(i));
  }
}
