//  ScaleFactorsManager.hpp
//
//  Created by Jeremi Niedziela on 01/11/2023.

#ifndef ScaleFactorsManager_hpp
#define ScaleFactorsManager_hpp

#include <nlohmann/json.hpp>

#include "Helpers.hpp"

#ifdef USE_CORRECTIONLIB
#include "correction.h"
using CorrectionRef = correction::Correction::Ref;
using CompoundCorrectionRef = correction::CompoundCorrection::Ref;
#else
struct DummyCorrectionRef {};
using CorrectionRef = DummyCorrectionRef;
using CompoundCorrectionRef = DummyCorrectionRef;
#endif

struct MuonID;
struct MuonIso;

class ScaleFactorsManager {
 public:
  static ScaleFactorsManager& GetInstance() {
    static ScaleFactorsManager* instance = new ScaleFactorsManager();
    return *instance;
  }

  ScaleFactorsManager(ScaleFactorsManager const&) = delete;
  void operator=(ScaleFactorsManager const&) = delete;

  std::map<std::string, float> GetPUJetIDScaleFactors(std::string name, float eta, float pt);
  std::map<std::string, float> GetMuonScaleFactors(std::string name, float eta, float pt);
  std::map<std::string, float> GetDSAMuonScaleFactors(std::string name, const std::vector<std::variant<int, double, std::string>>& args);
  std::map<std::string, float> GetMuonTriggerScaleFactors(std::string name, float eta, float pt);
  std::map<std::string, float> GetBTagScaleFactors(std::string name, float eta, float pt);

  std::map<std::string, float> GetPileupScaleFactorCustom(int nVertices);
  std::map<std::string, float> GetPileupScaleFactor(std::string name, float nVertices);

  std::vector<std::string> GetBTagVariationNames(std::string name);

  std::map<std::string, float> GetCustomScaleFactorsForCategory(std::string name, std::string category);
  std::map<std::string, float> GetCustomScaleFactors(std::string name, const std::vector<std::variant<int, double, std::string>>& args);

  std::map<std::string, float> GetDimuonScaleFactors(std::string name, const std::vector<std::variant<int, double, std::string>>& args);

  bool IsJetVetoMapDefined(std::string name);
  bool IsJetInBadRegion(std::string name, float eta, float phi);

  void ReadJetEnergyCorrections();
  bool ShouldApplyJetEnergyCorrections() { return ShouldApplyScaleFactor("jec") || ShouldApplyVariation("jec"); }
  std::map<std::string, float> GetJetEnergyCorrections(std::map<std::string, float> inputArguments);
  std::map<std::string, float> GetJetEnergyResolutionVariables(float jetEta, float jetPt, float rho);
  float GetJetEnergyResolutionPt(std::map<std::string, std::variant<int,double,std::string>> inputArguments);

  bool ShouldApplyScaleFactor(const std::string& name);
  bool ShouldApplyVariation(const std::string& name);

 private:
  ScaleFactorsManager();
  ~ScaleFactorsManager() {}

  static ScaleFactorsManager& getInstanceImpl() {
    static ScaleFactorsManager instance;
    return instance;
  }
  std::map<std::string, std::vector<bool>> applyScaleFactors;

  std::map<std::string, CorrectionRef> corrections;
  std::map<std::string, CompoundCorrectionRef> compoundCorrections;
  std::map<std::string, std::map<std::string, std::string>> correctionsExtraArgs;

  std::map<std::string, std::map<std::string, std::pair<double, double>>> boundsPerInput;

  TH1D* pileupSFvalues;

  void ExtractBounds(const nlohmann::json& node, std::map<std::string, std::pair<double, double>>& bounds);

  void ReadScaleFactorFlags();
  void ReadScaleFactors();
  void ReadPileupSFs();

  float TryToEvaluate(const std::string& name, const std::vector<std::variant<int, double, std::string>>& args);

  std::vector<std::string> GetScaleFactorVariations(std::string variations_str);
  std::map<std::string, std::pair<double, double>> GetInputBounds(std::map<std::string, std::string> extraArgs);
};

struct MuonID {
  MuonID(bool soft_, bool highPt_, bool trkHighPt_, bool tight_, bool mediumPrompt_, bool medium_, bool loose_)
      : soft(soft_), highPt(highPt_), trkHighPt(trkHighPt_), tight(tight_), mediumPrompt(mediumPrompt_), medium(medium_), loose(loose_) {}

  bool soft;
  bool highPt;
  bool trkHighPt;
  bool tight;
  bool mediumPrompt;
  bool medium;
  bool loose;

  bool PassesAnyId() { return soft || highPt || trkHighPt || tight || mediumPrompt || medium || loose; }

  std::string ToString() {
    std::string name = "";
    if (soft) name += "soft ";
    if (highPt) name += "highPt ";
    if (trkHighPt) name += "trkHighPt ";
    if (tight) name += "tight ";
    if (mediumPrompt) name += "mediumPrompt ";
    if (medium) name += "medium ";
    if (loose) name += "loose ";
    return name;
  }

  void Print() { info() << ToString() << std::endl; }
};

struct MuonIso {
  MuonIso(bool _tkIsoLoose, bool _tkIsoTight, bool _pFIsoVeryLoose, bool _pFIsoLoose, bool _pFIsoMedium, bool _pFIsoTight,
          bool _pFIsoVeryTight, bool _pFIsoVeryVeryTight)
      : tkIsoLoose(_tkIsoLoose),
        tkIsoTight(_tkIsoTight),
        pFIsoVeryLoose(_pFIsoVeryLoose),
        pFIsoLoose(_pFIsoLoose),
        pFIsoMedium(_pFIsoMedium),
        pFIsoTight(_pFIsoTight),
        pFIsoVeryTight(_pFIsoVeryTight),
        pFIsoVeryVeryTight(_pFIsoVeryVeryTight) {}

  bool tkIsoLoose;
  bool tkIsoTight;
  bool pFIsoVeryLoose;
  bool pFIsoLoose;
  bool pFIsoMedium;
  bool pFIsoTight;
  bool pFIsoVeryTight;
  bool pFIsoVeryVeryTight;

  bool PassesAnyIso() {
    return tkIsoLoose || tkIsoTight || pFIsoVeryLoose || pFIsoLoose || pFIsoMedium || pFIsoTight || pFIsoVeryTight || pFIsoVeryVeryTight;
  }

  std::string ToString() {
    std::string name = "";
    if (tkIsoLoose) name += "tkIsoLoose ";
    if (tkIsoTight) name += "tkIsoTight ";
    if (pFIsoVeryLoose) name += "pFIsoVeryLoose ";
    if (pFIsoLoose) name += "pFIsoLoose ";
    if (pFIsoMedium) name += "pFIsoMedium ";
    if (pFIsoTight) name += "pFIsoTight ";
    if (pFIsoVeryTight) name += "pFIsoVeryTight ";
    if (pFIsoVeryVeryTight) name += "pFIsoVeryVeryTight ";
    return name;
  }

  void Print() { info() << ToString() << std::endl; }
  // Muon_pfIsoId : UChar_t PFIso ID from miniAOD selector (1=PFIsoVeryLoose, 2=PFIsoLoose, 3=PFIsoMedium, 4=PFIsoTight, 5=PFIsoVeryTight,
  // 6=PFIsoVeryVeryTight)
  // Muon_tkIsoId : UChar_t TkIso ID (1=TkIsoLoose, 2=TkIsoTight)

  // Muon_miniIsoId : UChar_t MiniIso ID from miniAOD selector (1=MiniIsoLoose, 2=MiniIsoMedium, 3=MiniIsoTight, 4=MiniIsoVeryTight)
  // Muon_multiIsoId : UChar_t MultiIsoId from miniAOD selector (1=MultiIsoLoose, 2=MultiIsoMedium)
  // Muon_puppiIsoId : UChar_t PuppiIsoId from miniAOD selector (1=Loose, 2=Medium, 3=Tight)
};

#endif /* ScaleFactorsManager_hpp */