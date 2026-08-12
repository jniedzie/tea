//  AddedBranches.hpp
//
//  Owns the "branchesToAdd" config specs and one TTreeFormula per non-empty varexp, pre-filling
//  Event/PhysicsObject custom values for every visited event before app code runs.

#ifndef AddedBranches_hpp
#define AddedBranches_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class TTreeFormula;

class AddedBranches {
 public:
  AddedBranches();
  ~AddedBranches();

  // Compiles a TTreeFormula for every spec with a non-empty varexp, against whichever tree in
  // eventsTreeNames actually resolves it. fatal()s at setup on an unknown branch, a declared
  // type outside the nine supported ROOT scalar types, or a static multiplicity mismatch
  // (event-level branch with a per-object varexp, or vice versa).
  void Setup(const std::vector<std::string> &eventsTreeNames, const std::map<std::string, TTree *> &inputTrees);

  // Pre-fills every spec with a non-empty varexp onto the current event/objects. Must run after
  // the event's collections have their visible size set (ChangeVisibleSize) and after
  // AddExtraCollections, so per-object varexps see the same objects the app will.
  void Evaluate(const std::shared_ptr<Event> &event);

  const std::vector<AddedBranchParams> &GetSpecs() const { return specs; }
  bool Empty() const { return specs.empty(); }

 private:
  std::vector<AddedBranchParams> specs;
  std::map<std::string, TTreeFormula *> formulas;  // keyed by BranchName(), only for non-empty varexp

  void EvaluateScalar(const AddedBranchParams &spec, TTreeFormula *formula, const std::shared_ptr<Event> &event);
  void EvaluateArray(const AddedBranchParams &spec, TTreeFormula *formula, const std::shared_ptr<Event> &event);
};

#endif /* AddedBranches_hpp */
