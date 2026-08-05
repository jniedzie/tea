//  NanoEventProcessor.hpp
//
//  Created by Jeremi Niedziela on 24/11/2023.

#ifndef NanoEventProcessor_hpp
#define NanoEventProcessor_hpp

#include "Event.hpp"
#include "ExtensionsHelpers.hpp"
#include "EventProcessor.hpp"
#include "NanoMuon.hpp" 
#include "CutFlowManager.hpp"

class NanoEventProcessor {
 public:
  NanoEventProcessor();

  bool PassesEventCuts(const std::shared_ptr<NanoEvent> event, std::shared_ptr<CutFlowManager> cutFlowManager);

  float GetGenWeight(const std::shared_ptr<NanoEvent> event);
  std::map<std::string, float> GetL1PreFiringWeight(const std::shared_ptr<NanoEvent> event, std::string name);
  std::map<std::string,float> GetPileupScaleFactor(const std::shared_ptr<NanoEvent> event, std::string name);
  std::map<std::string,float> GetMuonTriggerScaleFactors(const std::shared_ptr<NanoEvent> event, std::string name);
  std::map<std::string,float> GetMediumBTaggingScaleFactors(const std::shared_ptr<NanoJets> b_jets);
  std::map<std::string,float> GetPUJetIDScaleFactors(const std::shared_ptr<NanoJets> jets);
  std::map<std::string,float> GetMuonScaleFactors(const std::shared_ptr<NanoMuons> looseMuonCollection);
  std::map<std::string,float> GetDSAMuonEfficiencyScaleFactors(const std::shared_ptr<NanoMuons> muonCollection);

  std::pair<std::shared_ptr<NanoMuon>, std::shared_ptr<NanoMuon>> GetMuonPairClosestToZ(const std::shared_ptr<NanoEvent> event, std::string collection);

  bool IsDataEvent(const std::shared_ptr<NanoEvent> event);

  float PropagateMET(const std::shared_ptr<NanoEvent> event, float totalDeltaPx, float totalDeltaPy);

  /***
  * Calculates jet and MET energy scale uncertainties for a given event.
  * allJetsCollectionName, goodJetsCollectionName, goodBJetsCollectionName are names for the collections including all jets, all good jets, and all good b-jets in the event.
  * goodJetCuts, goodBJetCuts, metPtCuts include the cut specifications for jets, b-jets and MET, given as pairs of min cut, max cut.
  * @return tuple of scale factors with up/down uncertainties for Jet energy scale uncertainties and MET, in this order.
  ***/
  std::tuple<std::map<std::string, float>,std::map<std::string, float>> GetJetMETEnergyScaleUncertainties(const std::shared_ptr<NanoEvent> event, 
    std::string allJetsCollectionName, std::string goodJetsCollectionName, std::string goodBJetsCollectionName,
    std::pair<float,float> goodJetCuts, std::pair<float,float> goodBJetCuts, std::pair<float,float> metPtCuts);

  void ApplyJetEnergyResolution(const std::shared_ptr<NanoEvent> event);
  
  /***
  * Calculates jet and MET energy scale uncertainties for a given event.
  * allJetsCollectionName, goodJetsCollectionName, goodBJetsCollectionName are names for the collections including all jets, all good jets, and all good b-jets in the event.
  * goodJetCuts, goodBJetCuts, metPtCuts include the cut specifications for jets, b-jets and MET, given as pairs of min cut, max cut.
  * @return tuple of scale factors with up/down uncertainties for Jet energy resolution uncertainties and MET, in this order.
  ***/
  std::tuple<std::map<std::string, float>,std::map<std::string, float>> GetJetMETEnergyResolutionUncertainties(const std::shared_ptr<NanoEvent> event, 
    std::string allJetsCollectionName, std::string goodJetsCollectionName, std::string goodBJetsCollectionName,
    std::pair<float,float> goodJetCuts, std::pair<float,float> goodBJetCuts, std::pair<float,float> metPtCuts);

 private:
  std::unique_ptr<EventProcessor> eventProcessor;
  std::vector<std::pair<std::string, std::pair<float, float>>> eventCuts;
  
  std::string weightsBranchName;
  std::string year;
  std::string rhoBranchName;
  std::string eventIDBranchName;

  // Updates up and down variation weights in weightsToUpdate with the systematic weight in alreadyUpdatedWeights, and skips any up/down variations in alreadyUpdatedWeights.
  void UpdateVariationWeights(std::map<std::string, float>& weightsToUpdate, std::map<std::string, float>& alreadyUpdatedWeights);

  // Returns pairs of cuts (pt_min, pt_max) for (goodJetsCollectionName,goodBJetsCollectionName)
  std::tuple<std::pair<float, float>,std::pair<float, float>> GetJetPtCuts(const std::shared_ptr<NanoEvent> event, std::string goodJetsCollectionName, std::string goodBJetsCollectionName);

  // Updates number of passing (b) jets in maps nPassingGoodJets and nPassingGoodBJets for a new jet pT newJetPt and map name.
  void UpdateNPassingJetsForPt(float newJetPt, std::string name,
    std::map<std::string,int>& nPassingGoodJets, std::map<std::string,int>& nPassingGoodBJets, 
    std::pair<float, float> goodJetPtCuts, std::pair<float, float> goodBJetPtCuts,
    bool isGoodJet, bool isGoodBJet);
  
  // Updates total momenta difference in x and y in maps: totalPxDifference and totalPyDifference for a new and old jet pT newJetPt, oldJetPt and map name.
  void UpdateMETDifferenceForPt(const std::shared_ptr<NanoJet> nanoJet, float newJetPt, float oldJetPt, std::string name,
    std::map<std::string,float>& totalPxDifference, std::map<std::string,float>& totalPyDifference);

  // Updataes the Jet SF for Jet Energy Corrections to 0 or 1 based on if the event passes the goodJetCuts and goodJetBCuts
  void UpdateSFsForJetJEC(std::map<std::string, float>& jecSFs, std::map<std::string,int> nPassingGoodJets, std::map<std::string,int> nPassingGoodBJets,
    std::pair<float,float> goodJetCuts, std::pair<float,float> goodBJetCuts);
  
  // Updataes the MET SF for Jet Energy Corrections to 0 or 1 based on if the event passes the metSFs
  void UpdateSFsForMETJEC(const std::shared_ptr<NanoEvent> event, std::map<std::string, float>& metSFs, 
    std::map<std::string,float> totalPxDifference, std::map<std::string,float> totalPyDifference, std::pair<float,float> metPtCuts);
  
};

#endif /* NanoEventProcessor_hpp */
