//  AddedBranches.hpp

#ifndef AddedBranches_hpp
#define AddedBranches_hpp

#include "Event.hpp"
#include "Helpers.hpp"

class TTreeFormula;

class AddedBranches {
 public:
  AddedBranches();
  ~AddedBranches();

  void Setup(const std::vector<std::string> &eventsTreeNames, const std::map<std::string, TTree *> &inputTrees);

  // Must run after the event's collections have their visible size set (ChangeVisibleSize) and
  // after AddExtraCollections, so per-object varexps see the same objects the app will.
  void Evaluate(const std::shared_ptr<Event> &event);

  const std::vector<AddedBranchParams> &GetSpecs() const { return specs; }
  bool Empty() const { return specs.empty(); }

 private:
  std::vector<AddedBranchParams> specs;
  std::map<std::string, TTreeFormula *> formulas;

  void EvaluateScalar(const AddedBranchParams &spec, TTreeFormula *formula, const std::shared_ptr<Event> &event);
  void EvaluateArray(const AddedBranchParams &spec, TTreeFormula *formula, const std::shared_ptr<Event> &event);
};

#endif /* AddedBranches_hpp */
