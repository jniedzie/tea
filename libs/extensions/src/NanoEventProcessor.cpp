//  NanoEventProcessor.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "NanoEventProcessor.hpp"

using namespace std;

NanoEventProcessor::NanoEventProcessor() {
  eventProcessor = make_unique<EventProcessor>();
  auto &config = ConfigManager::GetInstance();

  try {
    config.GetValue("weightsBranchName", weightsBranchName);
  } catch (const Exception &e) {
    warn() << "Weights branch not specified -- will assume weight is 1 for all events" << endl;
  }
  try {
    config.GetValue("year", year);
  } catch (const Exception &e) {
    info() << "Couldn't read year from config file - will assume year 2018" << endl;
    year = "2018";
  }
}

float NanoEventProcessor::GetGenWeight(const std::shared_ptr<NanoEvent> event) {
  float weight = 1.0;
  if (weightsBranchName.empty()) return weight;
  try {
    weight = event->Get(weightsBranchName);
  } catch (const Exception &e) {
    warn() << "NanoEventProcessor failed to get gen weight from branch: " << weightsBranchName << endl;
  }
  return weight;
}

float NanoEventProcessor::GetPileupScaleFactor(const std::shared_ptr<NanoEvent> event, string name) {
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  if (name == "custom") {
    int nVertices = event->GetAs<int>("PV_npvsGood");
    return scaleFactorsManager.GetPileupScaleFactorCustom(nVertices);
  } else {
    float nVertices = event->Get("Pileup_nTrueInt");
    return scaleFactorsManager.GetPileupScaleFactor(name, nVertices);
  }
}

map<string,float> NanoEventProcessor::GetMuonTriggerScaleFactors(const shared_ptr<NanoEvent> event, string name) {
  map<string,float> weights;
  if (!event->GetMuonTriggerScaleFactors().empty()) return event->GetMuonTriggerScaleFactors();

  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();

  auto leadingMuon = asNanoMuon(eventProcessor->GetMaxPtObject(event->GetEvent(), "Muon"));
  if(!leadingMuon) {
    warn() << "No leading muon found in event -- will assume SF=1.0" << endl;
    return {{"systematic", 1.0}};
  }
  weights = scaleFactorsManager.GetMuonTriggerScaleFactors(name, leadingMuon->GetEta(), leadingMuon->GetPt());
  event->SetMuonTriggerScaleFactors(weights);

  return weights;
}

map<string,float> NanoEventProcessor::GetMediumBTaggingScaleFactors(const shared_ptr<NanoJets> b_jets) {
  map<string,float> weights;
  bool firstIteration = true;
  for (auto b_jet : * b_jets) {
    map<string,float> weights_ = b_jet->GetBtaggingScaleFactors("bTaggingMedium");
    if (firstIteration) {
      weights = weights_;
      firstIteration = false;
      continue;
    }
    for (auto &[name, weight] : weights_) {
      weights[name] *= weight;
    }
  }
  // special case for 0 b-jets but we still need all variation names for histograms
  if (b_jets->size() == 0) {
    weights["systematic"] = 1.0;
    auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
    auto variations = scaleFactorsManager.GetBTagVariationNames("bTaggingMedium");
    for (auto variation : variations) {
      weights["bTaggingMedium_"+variation] = 1.0;
    }
  }
  return weights;
}

map<string,float> NanoEventProcessor::GetPUJetIDScaleFactors(const shared_ptr<NanoJets> jets) {
  map<string,float> weights;
  bool firstIteration = true;
  for (auto jet : * jets) {
    map<string,float> weights_ = jet->GetPUJetIDScaleFactors("PUjetIDtight");
    if (firstIteration) {
      weights = weights_;
      firstIteration = false;
      continue;
    }
    for (auto &[name, weight] : weights_) {
      weights[name] *= weight;
    }
  }
  return weights;
}

map<string,float> NanoEventProcessor::GetMuonScaleFactors(const std::shared_ptr<NanoMuons> muonCollection) {
  map<string,float> weights;
  bool firstIteration = true;
  for (auto muon : *muonCollection) {
    auto weights_loose = muon->GetScaleFactors("muonIDLoose", "muonIsoLoose", "muonReco", year);
    auto weights_tight = muon->GetScaleFactors("muonIDTight", "muonIsoTight", "muonReco", year);
    if (firstIteration) {
      for (auto &[name, weight] : weights_loose) weights[name] = 1.0;
      for (auto &[name, weight] : weights_tight) weights[name] = 1.0;
      firstIteration = false;
    }

    if (muon->IsTight()) {
      for (auto &[name, weight] : weights_tight) weights[name] *= weight;
    }
    else {
      for (auto &[name, weight] : weights_loose) weights[name] *= weight;
    }
  }
  return weights;
}

pair<shared_ptr<NanoMuon>, shared_ptr<NanoMuon>> NanoEventProcessor::GetMuonPairClosestToZ(const std::shared_ptr<NanoEvent> event,
                                                                                   string collection) {
  auto muons = event->GetCollection(collection);
  if (muons->size() < 2) return {nullptr, nullptr};

  shared_ptr<NanoMuon> muonA;
  shared_ptr<NanoMuon> muonB;

  double zMass = 91.1876;  // GeV
  double smallestDifferenceToZmass = 999999;
  double massClosestToZ = -1;

  for (int iMuon1 = 0; iMuon1 < muons->size(); iMuon1++) {
    auto muon1 = asNanoMuon(muons->at(iMuon1));
    auto muon1fourVector = muon1->GetFourVector();

    for (int iMuon2 = iMuon1 + 1; iMuon2 < muons->size(); iMuon2++) {
      auto muon2 = asNanoMuon(muons->at(iMuon2));
      auto muon2fourVector = muon2->GetFourVector();

      double diMuonMass = (muon1fourVector + muon2fourVector).M();
      if (fabs(diMuonMass - zMass) < smallestDifferenceToZmass) {
        smallestDifferenceToZmass = fabs(diMuonMass - zMass);
        muonA = muon1;
        muonB = muon2;
      }
    }
  }

  return {muonA, muonB};
}

bool NanoEventProcessor::IsDataEvent(const std::shared_ptr<NanoEvent> event) {
  // Test 1: gen wights branch only for MC
  bool isData = false;
  if (!weightsBranchName.empty()) {
    try {
      float genWeight = event->Get(weightsBranchName);
    } catch (const Exception &e) {
      isData = true;
    }
  }
  // Test 2: run run = 1 for MC
  int run = event->GetAs<int>("run");
  if (run == 1) {
    if (isData) {
      fatal() << "Conflicting NanoEventProcessor::IsDataEvent results.";
      exit(0);
    }
    return false;
  }
  if (!isData) {
    fatal() << "Conflicting NanoEventProcessor::IsDataEvent results.";
    exit(0);
  }
  return true;
}

map<string,vector<float>> NanoEventProcessor::GetJetEnergyCorrections(shared_ptr<NanoEvent> event, string inputCollectionName) {
  map<string,vector<float>> correctedJetPts;
  
  auto &scaleFactorsManager = ScaleFactorsManager::GetInstance();
  scaleFactorsManager.ReadJetEnergyCorrections();
  if (!scaleFactorsManager.ShouldApplyJetEnergyCorrections())
    return correctedJetPts;

  shared_ptr<PhysicsObjects> jetCollection;
  try{
    jetCollection = event->GetCollection(inputCollectionName);
  }
  catch(Exception &e){
    error() << "Couldn't find collection " << inputCollectionName << " for jet energy corrections." << endl;
    return correctedJetPts;
  }

  auto &config = ConfigManager::GetInstance();
  string rhoBranchName;
  try {
    config.GetValue("rhoBranchName", rhoBranchName);
  } catch (const Exception &e) {
    warn() << "Rho branch not specified -- will assume standard name fixedGridRhoFastjetAll" << endl;
    rhoBranchName = "fixedGridRhoFastjetAll";
  }
  float rho = event->Get(rhoBranchName);  
  map<string, float> inputs = {{"Rho", rho}};
  map<string, vector<float>> jetPtVariations;
  map<string,int> nPassingJets;
  map<string, pair<float,float>> metVariations;
  for (auto jet : *jetCollection) {

    map<string,float> ptCorrections = asNanoJet(jet)->GetJetEnergyCorrectionPtVariations(rho);
    for (auto &[name, ptCorrection] : ptCorrections) {
      if (name == "systematic") continue;

      if (correctedJetPts.find(name) == correctedJetPts.end()) {
        correctedJetPts[name] = std::vector<float>{ptCorrection};
      }
      else {
        correctedJetPts[name].push_back(ptCorrection);
      }
    }
  }
  return correctedJetPts;
}

pair<float,float> NanoEventProcessor::PropagateMET(float oldJet_pt, float newJet_pt, float jet_phi, float met_pt, float met_phi) {
  // Calculate the change in MET due to the jet pt and phi change
  float dMET_x = newJet_pt * cos(jet_phi) - oldJet_pt * cos(jet_phi);
  float dMET_y = newJet_pt * sin(jet_phi) - oldJet_pt * sin(jet_phi);

  // Update MET
  float newMET_px = met_pt * cos(met_phi) - dMET_x;
  float newMET_py = met_pt * sin(met_phi) - dMET_y;
  float newMET_pt = sqrt(newMET_px * newMET_px + newMET_py * newMET_py); 
  float newMET_phi = atan2(newMET_py, newMET_px);

  return make_pair(newMET_pt, newMET_phi);
}
