//  Event.cpp
//
//  Created by Jeremi Niedziela on 04/08/2023.

#include "Event.hpp"

#include "EventProcessor.hpp"
#include "Helpers.hpp"

using namespace std;

#include "Helpers.hpp"

using namespace std;

Event::Event() {
  try {
    config.GetExtraEventCollections(extraCollectionsDescriptions);
  } catch (const Exception& e) {
    hasExtraCollections = false;
  }

  double xedges[83] = {-5.191, -4.889, -4.716, -4.538, -4.363, -4.191, -4.013, -3.839, -3.664, -3.489, -3.314, -3.139, -2.964, -2.853,
                       -2.65,  -2.5,   -2.322, -2.172, -2.043, -1.93,  -1.83,  -1.74,  -1.653, -1.566, -1.479, -1.392, -1.305, -1.218,
                       -1.131, -1.044, -0.957, -0.879, -0.783, -0.696, -0.609, -0.522, -0.435, -0.348, -0.261, -0.174, -0.087, 0,
                       0.087,  0.174,  0.261,  0.348,  0.435,  0.522,  0.609,  0.696,  0.783,  0.879,  0.957,  1.044,  1.131,  1.218,
                       1.305,  1.392,  1.479,  1.566,  1.653,  1.74,   1.83,   1.93,   2.043,  2.172,  2.322,  2.5,    2.65,   2.853,
                       2.964,  3.139,  3.314,  3.489,  3.664,  3.839,  4.013,  4.191,  4.363,  4.538,  4.716,  4.889,  5.191};

  jetMapNoVeto = make_unique<TH2D>("jetMapNoVeto", "jetMapNoVeto", 82, xedges, 72, -TMath::Pi(), TMath::Pi());
  jetMapWithVeto = make_unique<TH2D>("jetMapWithVeto", "jetMapWithVeto", 82, xedges, 72, -TMath::Pi(), TMath::Pi());
}

Event::~Event() {
  if (jetMapNoVeto->GetEntries() != 0) jetMapNoVeto->SaveAs("jetMapNoVeto.root");
  if (jetMapWithVeto->GetEntries() != 0) jetMapWithVeto->SaveAs("jetMapWithVeto.root");
}

void Event::Reset() { extraCollections.clear(); }

template <typename First, typename... Rest>
bool Event::tryGet(shared_ptr<PhysicsObject> physicsObject, string branchName, pair<float, float> cuts) {
  try {
    First value = physicsObject->Get(branchName);
    return value >= cuts.first && value <= cuts.second;
  } catch (BadTypeException& e) {
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

void Event::AddExtraCollections() {
  if (!hasExtraCollections) return;

  for (auto& [name, extraCollection] : extraCollectionsDescriptions) {
    auto newCollection = make_shared<PhysicsObjects>();

    for (auto inputCollectionName : extraCollection.inputCollections) {
      shared_ptr<PhysicsObjects> inputCollection;

      try {
        inputCollection = GetCollection(inputCollectionName);
      } catch (const Exception& e) {
        error() << "Couldn't find collection " << inputCollectionName << " for extra collection " << name << endl;
        continue;
      }

      for (auto physicsObject : *inputCollection) {
        bool passes = true;

        for (auto& [branchName, flag] : extraCollection.flags) {
          passes = checkCuts(physicsObject, branchName, {flag, flag});
          if (!passes) break;
        }
        if (!passes) continue;

        for (auto& [branchName, cuts] : extraCollection.allCuts) {
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

bool Event::PassesHEMveto(float affectedFraction) {
  // Implemented based on the recommendations from:
  // https://cms-talk.web.cern.ch/t/question-about-hem15-16-issue-in-2018-ultra-legacy/38654?u=gagarwal

  if (config.GetYear() != "2018") return true;  // HEM veto only applies to 2018 data/MC

  if (!IsData()) {
    float randNum = randFloat();
    if (randNum > affectedFraction) {
      return true;
    }
  } else {
    unsigned runNumber = Get("run");
    if (runNumber < 319077) {
      warn() << "Run number less than 319077 found in 2018 data/MC. HEM veto will not be applied for this event." << endl;
      return true;  // HEM veto only applies to runs >= 319077
    }
  }

  auto jets = GetCollection("Jet");
  auto muons = GetCollection("Muon");

  for (auto& jet : *jets) {
    // jet pT > 15 GeV
    float jetPt = jet->Get("pt");
    if (jetPt < 15) continue;

    // tight jet ID with lep veto OR [tight jet ID & (jet EM fraction < 0.9) & (jets that don’t overlap with PF muon (dR < 0.2)]
    int jetID = jet->Get("jetId");

    bool overlapsWithMuon = false;
    auto jetVector = jet->GetFourVector();

    for (auto& muon : *muons) {
      auto muonVector = muon->GetFourVector();
      float dR = jetVector.DeltaR(muonVector);
      if (dR < 0.2) {
        overlapsWithMuon = true;
        break;
      }
    }
    float jetEmEF = jet->GetAs<float>("chEmEF") + jet->GetAs<float>("neEmEF");

    // bit1 is loose (always false in 2017 since it does not exist), bit2 is tight, bit3 is tightLepVeto*
    bool passesID = (jetID & 0b100) || ((jetID & 0b010) && (jetEmEF < 0.9) && !overlapsWithMuon);
    if (!passesID) continue;

    // PU jet ID for AK4chs jets with pT < 50 GeV (No PUjetID required for PUPPI jets)
    int jetPUid = jet->Get("puId");
    if (jetPt < 50 && jetPUid == 0) continue;

    // check if jet is in HEM region
    // jets with -1.57 <phi< -0.87 and -2.5<eta<-1.3
    // jets with -1.57 <phi< -0.87 and -3.0<eta<-2.5

    if (jetVector.Eta() >= -3.0 && jetVector.Eta() <= -1.3 && jetVector.Phi() >= -1.57 && jetVector.Phi() <= -0.87) {
      return false;
    }
  }
  return true;
}

bool Event::PassesJetVetoMaps(bool saveHistograms) {
  // Implemented based on the recommendations from:
  // https://cms-jerc.web.cern.ch/Recommendations/#jet-veto-maps

  string year = config.GetYear();
  if (!scaleFactorsManager.IsJetVetoMapDefined("jetVetoMaps_" + year)) return true;

  auto jets = GetCollection("Jet");

  for (auto& jet : *jets) {
    // jet pT > 15 GeV
    float jetPt = jet->Get("pt");
    if (jetPt < 15) continue;

    // tightLepVeto jet ID
    unsigned char jetID = jet->Get("jetId");
    bool passesID = (jetID & 0b100);
    if (!passesID) continue;

    // (jet charged EM fraction + jet neutral EM fraction) < 0.9
    float jetEmEF = jet->GetAs<float>("chEmEF") + jet->GetAs<float>("neEmEF");
    if (jetEmEF >= 0.9) continue;

    float jetEta = jet->Get("eta");
    float jetPhi = jet->Get("phi");

    if (saveHistograms) jetMapNoVeto->Fill(jetEta, jetPhi);
    if (scaleFactorsManager.IsJetInBadRegion("jetVetoMaps_" + year, jetEta, jetPhi)) return false;
    if (saveHistograms) jetMapWithVeto->Fill(jetEta, jetPhi);
  }
  return true;
}

bool Event::IsData() {
  // Test 1: gen weights branch only for MC
  bool isData = false;
  string weightsBranchName;
  config.GetValue("weightsBranchName", weightsBranchName);
  try {
    Get(weightsBranchName);
  } catch (const Exception& e) {
    isData = true;
  }

  // Test 2: run run = 1 for MC
  unsigned run = Get("run");
  if (run == 1) {
    if (isData) {
      fatal() << "Conflicting Event::IsData results.";
      exit(0);
    }
    return false;
  }
  if (!isData) {
    fatal() << "Conflicting Event::IsData results.";
    exit(0);
  }
  return true;
}
