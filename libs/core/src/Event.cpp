//  Event.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "Event.hpp"

#include "EventProcessor.hpp"
#include "Helpers.hpp"
#include "ScaleFactorsManager.hpp"

using namespace std;

#include "Helpers.hpp"

using namespace std;

Event::Event() {
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetExtraEventCollections(extraCollectionsDescriptions);
  } catch (const Exception &e) {
    info() << "No extra event collections found" << endl;
    hasExtraCollections = false;
  }
  try {
    config.GetValue("rhoBranchName", rhoBranchName);
  } catch (const Exception &e) {
    warn() << "Rho branch not specified -- will assume standard name fixedGridRhoFastjetAll" << endl;
    rhoBranchName = "fixedGridRhoFastjetAll";
  }
}

Event::~Event() {}

void Event::Reset() { extraCollections.clear(); }

template <typename First, typename... Rest>
bool Event::tryGet(shared_ptr<PhysicsObject> physicsObject, string branchName, pair<float, float> cuts) {
  try {
    First value = physicsObject->Get(branchName);
    return value >= cuts.first && value <= cuts.second;
  } catch (BadTypeException &e) {
    if constexpr (sizeof...(Rest) > 0) {
      return tryGet<Rest...>(physicsObject, branchName, cuts);
    } else {
      fatal() << e.what() << endl;
      gErrorIgnoreLevel = kFatal;
      exit(0);
    }
  }
}

bool Event::checkCuts(shared_ptr<PhysicsObject> physicsObject, string branchName, pair<float, float> cuts) {
  // important: checking float first makes things much faster, since most branches are floats
  return tryGet<Float_t, Bool_t, UChar_t, UInt_t, Int_t, UShort_t, Short_t>(physicsObject, branchName, cuts);
}

void Event::AddJetEnergyCorrections() {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  scaleFactorsManager.ReadJetEnergyCorrections();

  if (!scaleFactorsManager.ApplyJetEnergyCorrections()) return;

  string jetCollectionName = "Jet"; // make configurable?
  shared_ptr<PhysicsObjects> inputCollection;
  try{
    inputCollection = GetCollection(jetCollectionName);
  }
  catch(Exception &e){
    error() << "Couldn't find collection " << jetCollectionName << " for jet energy corrections." << endl;
    return;
  }

  float rho = Get(rhoBranchName);  
  map<string, float> inputs = {{"Rho", rho}};
  map<pair<string,string>,float> totalJetPts;
  for (auto physicsObject : *inputCollection) {
    float pt = physicsObject->Get("pt");
    float rawFactor = physicsObject->Get("rawFactor");
    float rawPt = pt * (1 - rawFactor);
    inputs["JetA"] = (float)physicsObject->Get("area");
    inputs["JetEta"] = (float)physicsObject->Get("eta");
    inputs["JetPt"] = rawPt;
    inputs["JetMass"] = (float)physicsObject->Get("mass");
    inputs["JetPhi"] = (float)physicsObject->Get("phi");
    map<string,float> corrections = scaleFactorsManager.GetJetEnergyCorrections(inputs);
    float jecPt = pt*corrections["systematic"];
    physicsObject->AddVariable("jecFactor", corrections["systematic"]);
    physicsObject->AddVariable("jecPt", jecPt);
    cout << "jecPt: " << jecPt << " , " << (float)physicsObject->Get("jecPt") << endl;
    cout << "jecFactor: " << corrections["systematic"] << " , " << (float)physicsObject->Get("jecFactor") << endl;
    map<pair<string,string>,float> jetPts;
    for (auto &[name, correction] : corrections) {
      if (totalJetPts.find(make_pair(name,"systematic")) == totalJetPts.end()) totalJetPts[make_pair(name,"systematic")] = pt * correction;
      else totalJetPts[make_pair(name,"systematic")] += pt * correction;
      if (totalJetPts.find(make_pair(name,"up")) == totalJetPts.end()) totalJetPts[make_pair(name,"up")] = pt * (1 + correction);
      else totalJetPts[make_pair(name,"up")] += pt * (1 + correction);
      if (totalJetPts.find(make_pair(name,"down")) == totalJetPts.end()) totalJetPts[make_pair(name,"down")] = pt * (1 - correction);
      else totalJetPts[make_pair(name,"down")] += pt * (1 - correction);
      if (name == "systematic") continue;
      
      jetPts[make_pair(name,"up")] = pt * (1 + correction);
      jetPts[make_pair(name,"down")] = pt * (1 - correction);
    }
  }
}

void Event::AddExtraCollections() {
  if (!hasExtraCollections) return;

  for (auto &[name, extraCollection] : extraCollectionsDescriptions) {
    auto newCollection = make_shared<PhysicsObjects>();

    for (auto inputCollectionName : extraCollection.inputCollections) {
      
      shared_ptr<PhysicsObjects> inputCollection; 
      
      try{
        inputCollection = GetCollection(inputCollectionName);
      }
      catch(Exception &e){
        error() << "Couldn't find collection " << inputCollectionName << " for extra collection " << name << endl;
        continue;
      }

      for (auto physicsObject : *inputCollection) {
        bool passes = true;

        for (auto &[branchName, flag] : extraCollection.flags) {
          passes = checkCuts(physicsObject, branchName, {flag, flag});
          if (!passes) break;
        }
        if (!passes) continue;

        for (auto &[branchName, cuts] : extraCollection.allCuts) {
          passes = checkCuts(physicsObject, branchName, cuts);
          if (!passes) break;
        }
        if (!passes) continue;

        newCollection->push_back(physicsObject);
      }
    }
    extraCollections.insert({name, newCollection});
  }
}
