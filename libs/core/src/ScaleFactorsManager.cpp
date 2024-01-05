//  ScaleFactorsManager.cpp
//
//  Created by Jeremi Niedziela on 01/11/2023.

#include "ScaleFactorsManager.hpp"

#include "ConfigManager.hpp"
#include "correction.h"

using namespace std;

ScaleFactorsManager::ScaleFactorsManager() {
  ReadScaleFactorFlags();
  if (applyScaleFactors["muon"] || applyScaleFactors["muonTrigger"]) ReadMuonSFs();
  if (applyScaleFactors["pileup"]) ReadPileupSFs();
  if (applyScaleFactors["bTagging"]) ReadBtaggingSFs();
}

void ScaleFactorsManager::ReadScaleFactorFlags() {
  auto &config = ConfigManager::GetInstance();
  config.GetMap("applyScaleFactors", applyScaleFactors);

  info() << "\n------------------------------------" << endl;
  info() << "Applying scale factors:" << endl;
  for (auto &[name, apply] : applyScaleFactors) {
    info() << "  " << name << ": " << apply << endl;
  }
  info() << "------------------------------------\n" << endl;
}

void ScaleFactorsManager::ReadMuonSFs() {
  auto &config = ConfigManager::GetInstance();

  map<string, ScaleFactorsMap> muonSFs;
  config.GetScaleFactors("muonSFs", muonSFs);

  for (auto &[name, values] : muonSFs) {
    string path = "../data/muon_SFs/" + name + ".root";
    if (!FileExists(path)) {
      ScaleFactorsMap muonSFs;
      CreateMuonSFsHistogram(values, path, name);
    }
    muonSFvalues[name] = (TH2D *)TFile::Open(path.c_str())->Get(name.c_str());
  }
}

void ScaleFactorsManager::ReadPileupSFs() {
  auto &config = ConfigManager::GetInstance();

  string pileupScaleFactorsPath, pileupScaleFactorsHistName;
  config.GetValue("pileupScaleFactorsPath", pileupScaleFactorsPath);
  config.GetValue("pileupScaleFactorsHistName", pileupScaleFactorsHistName);
  info() << "Reading pileup scale factors from file: " << pileupScaleFactorsPath << "\thistogram: " << pileupScaleFactorsHistName << endl;
  pileupSFvalues = (TH1D *)TFile::Open(pileupScaleFactorsPath.c_str())->Get(pileupScaleFactorsHistName.c_str());
}

void ScaleFactorsManager::ReadBtaggingSFs() {
  auto &config = ConfigManager::GetInstance();

  map<string, ScaleFactorsTuple> bTaggingSFs;
  config.GetScaleFactors("bTaggingSFs", bTaggingSFs);

  for (auto &[name, values] : bTaggingSFs) {
    string formula = get<0>(values);
    auto function = new TF1(name.c_str(), formula.c_str());
    vector<float> params = get<1>(values);
    for (int i = 0; i < params.size(); i++) {
      function->SetParameter(i, params[i]);
    }
    btaggingSFvalues[name] = function;
  }
}

void ScaleFactorsManager::CreateMuonSFsHistogram(const ScaleFactorsMap &muonSFs, string outputPath, string histName) {
  set<float> etaBinsSet, ptBinsSet;

  for (auto &[etaRange, valuesForEta] : muonSFs) {
    etaBinsSet.insert(get<0>(etaRange));
    etaBinsSet.insert(get<1>(etaRange));

    for (auto &[ptRange, values] : valuesForEta) {
      ptBinsSet.insert(get<0>(ptRange));
      ptBinsSet.insert(get<1>(ptRange));
    }
  }

  vector<float> etaBins(etaBinsSet.begin(), etaBinsSet.end());
  vector<float> ptBins(ptBinsSet.begin(), ptBinsSet.end());

  auto hist = new TH2D(histName.c_str(), histName.c_str(), etaBins.size() - 1, etaBins.data(), ptBins.size() - 1, ptBins.data());

  for (auto &[etaRange, valuesForEta] : muonSFs) {
    float eta = (get<1>(etaRange) + get<0>(etaRange)) / 2.;
    for (auto &[ptRange, values] : valuesForEta) {
      float pt = (get<1>(ptRange) + get<0>(ptRange)) / 2.;
      if (!values.count("value")) {
        error() << "Scale factor value for " << histName << " not defined for eta: " << eta << " pt: " << pt << endl;
      }
      hist->Fill(eta, pt, values.at("value"));
    }
  }
  makeParentDirectories(outputPath);
  hist->SaveAs(outputPath.c_str());
}

float ScaleFactorsManager::GetMuonRecoScaleFactor(float eta, float pt, string ptRange) {
  if (!applyScaleFactors["muon"]) return 1.0;

  string name = "";

  if (ptRange == "lowPt" || ptRange == "midPt") {
    name = "NUM_TrackerMuons_DEN_genTracks";
  } else if (ptRange == "highPt") {
    name = "NUM_GlobalMuons_DEN_TrackerMuons";
  } else {
    error() << "Muon reco SFs not defined for pt range: " << ptRange << endl;
    return 1;
  }

  return GetScaleFactor(name, eta, pt);
}

float ScaleFactorsManager::GetMuonIDScaleFactor(float eta, float pt, string id) {
  if (!applyScaleFactors["muon"]) return 1.0;

  // ID options:
  // SoftID
  // TightID
  // MediumID
  // LooseID
  // MediumPromptID
  // HighPtID
  // TrkHighPtID

  string name = "NUM_" + id + "_DEN_TrackerMuons";

  if (!muonSFvalues.count(name)) {
    warn() << "Muon ID SFs not defined for ID: " << id << endl;
    return 1;
  }
  return GetScaleFactor(name, eta, pt);
}

float ScaleFactorsManager::GetMuonIsoScaleFactor(float eta, float pt, string id, string iso) {
  if (!applyScaleFactors["muon"]) return 1.0;

  // ID options:
  // TrkHighPtID
  // HighPtID
  // TightID
  // MediumPromptID
  // MediumID
  // LooseID

  // Iso options:
  // TightRelTkIso
  // LooseRelTkIso
  // TightRelIso
  // LooseRelIso

  if (id == "TrkHighPtID" || id == "HighPtID" || id == "TightID") id += "andIPCut";
  string name = "NUM_" + iso + "_DEN_" + id;

  if (!muonSFvalues.count(name)) {
    warn() << "Muon Iso SFs not defined for combination of ID & Iso: " << id << " -- " << iso << endl;
    return 1;
  }
  return GetScaleFactor(name, eta, pt);
}

float ScaleFactorsManager::GetMuonTriggerScaleFactor(float eta, float pt, string id, string iso, string triggers) {
  if (!applyScaleFactors["muonTrigger"]) return 1.0;
  // ID options:
  // IdTight
  // IdMedium
  // IdGlobalHighPt

  // Iso options:
  // PFIsoTight
  // PFIsoMedium
  // TkIsoLoose

  // Trigger options:
  // IsoMu24
  // IsoMu24_or_Mu50
  // Mu50_or_OldMu100_or_TkMu100

  string name = "NUM_" + triggers + "_DEN_CutBased" + id + "_and_" + iso;

  if (!muonSFvalues.count(name)) {
    warn() << "Muon Trigger SFs not defined for combination of triggers & ID & Iso: " << triggers << " -- " << id << " -- " << iso << endl;
    return 1;
  }
  return GetScaleFactor(name, eta, pt);
}

float ScaleFactorsManager::GetScaleFactor(string name, float eta, float pt) {
  TH2D *hist = muonSFvalues[name];

  BringEtaPtToHistRange(hist, eta, pt);

  int etaBin = hist->GetXaxis()->FindBin(eta);
  int ptBin = hist->GetYaxis()->FindBin(pt);

  return hist->GetBinContent(etaBin, ptBin);
}

void ScaleFactorsManager::BringEtaPtToHistRange(TH2D *hist, float &eta, float &pt) {
  if (eta < hist->GetXaxis()->GetBinLowEdge(1)) {
    eta = hist->GetXaxis()->GetBinLowEdge(1) + 0.01;
  }
  if (eta > hist->GetXaxis()->GetBinUpEdge(hist->GetNbinsX())) {
    eta = hist->GetXaxis()->GetBinUpEdge(hist->GetNbinsX()) - 0.01;
  }

  if (pt < hist->GetYaxis()->GetBinLowEdge(1)) {
    pt = hist->GetYaxis()->GetBinLowEdge(1) + 0.01;
  }

  if (pt > hist->GetYaxis()->GetBinUpEdge(hist->GetNbinsY())) {
    pt = hist->GetYaxis()->GetBinUpEdge(hist->GetNbinsY()) - 0.01;
  }
}

float ScaleFactorsManager::GetPileupScaleFactor(int nVertices) {
  if (!applyScaleFactors["pileup"]) return 1.0;

  if (nVertices < pileupSFvalues->GetXaxis()->GetBinLowEdge(1)) {
    warn() << "Number of vertices is lower than the lowest bin edge in pileup SF histogram" << endl;
    return 1.0;
  }
  if (nVertices > pileupSFvalues->GetXaxis()->GetBinUpEdge(pileupSFvalues->GetNbinsX())) {
    warn() << "Number of vertices is higher than the highest bin edge in pileup SF histogram" << endl;
    return 1.0;
  }

  float sf = pileupSFvalues->GetBinContent(pileupSFvalues->FindFixBin(nVertices));
  return sf;
}

float ScaleFactorsManager::GetBTagScaleFactor(float pt, std::string ID) {
  if (!applyScaleFactors["b_tagging"]) return 1.0;

  if (pt < 20) {
    warn() << "Jet pt is lower than the lowest allowed value in b-tagging SF histogram" << endl;
    return 1.0;
  }
  if (pt > 1000) {
    warn() << "Jet pt is higher than the highest allowed value in b-tagging SF histogram" << endl;
    return 1.0;
  }

  float sf = btaggingSFvalues["deepJet_mujets_" + ID]->Eval(pt);
  return sf;
}
