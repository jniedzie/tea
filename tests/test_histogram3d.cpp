#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>

#include "ConfigManager.hpp"
#include "HistogramsHandler.hpp"

namespace {
bool Close(double actual, double expected) {
  return std::abs(actual - expected) < 1e-12;
}

int Fail(const std::string &message) {
  std::cerr << message << std::endl;
  return 1;
}
}  // namespace

int main(int argc, char **argv) {
  if (argc < 3 || argc > 4) { return Fail("Expected configuration, output path and optional error mode"); }
  setenv("TEA_TH3D_TEST_OUTPUT", argv[2], 1);
  setenv("TEA_TH3D_TEST_MODE", argc == 4 ? argv[3] : "", 1);
  ConfigManager::Initialize(argv[1]);
  auto handler = std::make_unique<HistogramsHandler>();
  if (argc == 4) {
    handler->Fill("unknown", 0.5, 0.5, 0.5);
    return Fail("An invalid fill unexpectedly succeeded");
  }

  if (handler->GetHistograms3D().size() != 5) { return Fail("Invalid TH3D definitions were not skipped"); }
  auto *volume = handler->GetHistogram3D({"volume", ""});
  auto *variable = handler->GetHistogram3D({"variable", ""});
  auto *top = handler->GetHistogram3D({"variable_top", ""});
  if (!volume || !variable || !top) { return Fail("TH3D getters did not return nominal objects"); }
  if (volume->GetNbinsX() != 2 || volume->GetNbinsY() != 3 || volume->GetNbinsZ() != 4 ||
      !Close(volume->GetXaxis()->GetXmin(), 0) || !Close(volume->GetXaxis()->GetXmax(), 2) ||
      !Close(volume->GetYaxis()->GetXmin(), -1) || !Close(volume->GetYaxis()->GetXmax(), 2) ||
      !Close(volume->GetZaxis()->GetXmin(), 10) || !Close(volume->GetZaxis()->GetXmax(), 14)) {
    return Fail("Regular TH3D axes are incorrect");
  }
  for (auto *histogram : {variable, top}) {
    if (histogram->GetNbinsX() != 2 || histogram->GetNbinsY() != 2 || histogram->GetNbinsZ() != 2 ||
        !Close(histogram->GetXaxis()->GetBinUpEdge(2), 3) || !Close(histogram->GetYaxis()->GetBinUpEdge(2), 4) ||
        !Close(histogram->GetZaxis()->GetBinUpEdge(2), 15)) {
      return Fail("Variable TH3D axes are incorrect");
    }
  }

  const auto fillRegressions = [&handler](double profileValue) {
    handler->Fill("regression_one", 0.5);
    handler->Fill("regression_variable", 0.5);
    handler->Fill("two", 0.5, 0.5);
    handler->Fill("two_variable", 0.5, 0.5);
    handler->Fill("profile", 0.5, 0.5, profileValue);
    handler->Fill("profile_variable", 0.5, 0.5, profileValue);
  };
  handler->Fill("volume", 0.5, 0.5, 10.5);
  handler->Fill("variable", 2, 2, 12);
  handler->Fill("variable_top", 2, 2, 12);
  fillRegressions(100);
  if (!Close(volume->GetBinContent(volume->FindBin(0.5, 0.5, 10.5)), 1)) {
    return Fail("Default TH3D event weight is incorrect");
  }
  handler->SetEventWeights({{"default", 2.0F}, {"up", 4.0F}, {"down", -1.0F}});
  auto *up = handler->GetHistogram3D({"volume", "up"});
  if (!up || up->GetEntries() != 0 || up->Integral() != 0 || up->GetSumOfWeights() != 0 || !Close(up->GetMean(1), 0)) {
    return Fail("TH3D variation cloned nominal entries or statistics");
  }
  if (std::string(up->GetName()) != "volume_up" || std::string(up->GetTitle()) != "volume_up") {
    return Fail("TH3D variation names or titles are incorrect");
  }
  if (handler->GetHistograms3D().size() != 11 || handler->GetHistograms3D().count({"unselected", "up"})) {
    return Fail("TH3D variation selection is incorrect");
  }

  handler->Fill("volume", 0.5, 0.5, 10.5);
  handler->Fill("variable", 2, 2, 12);
  handler->Fill("variable_top", 2, 2, 12);
  handler->Fill("unselected", 0.5, 0.5, 10.5);
  fillRegressions(10);
  handler->SetEventWeights({{"default", -1.0F}, {"up", 2.0F}, {"down", -2.0F}});
  handler->Fill("volume", 0.5, 0.5, 10.5);
  handler->Fill("variable", 2, 2, 12);
  handler->Fill("variable_top", 2, 2, 12);
  fillRegressions(4);
  for (const auto &name : {"volume", "variable", "variable_top"}) {
    const int bin = std::string(name) == "volume" ? volume->FindBin(0.5, 0.5, 10.5) : variable->FindBin(2, 2, 12);
    for (const auto &[variation, expected] : std::map<std::string, double>{{"", 2}, {"up", 6}, {"down", -3}}) {
      auto *histogram = handler->GetHistogram3D({name, variation});
      if (!histogram || !Close(histogram->GetBinContent(bin), expected)) {
        return Fail("TH3D event or variation weights are incorrect");
      }
    }
  }
  if (!Close(up->GetBinError(up->FindBin(0.5, 0.5, 10.5)), std::sqrt(20.0))) {
    return Fail("TH3D weighted bin errors are incorrect");
  }
  for (auto &[names, histogram] : handler->GetHistograms1D()) {
    const double expected = names.second.empty() ? 2 : names.second == "up" ? 6 : -3;
    if (!Close(histogram->GetBinContent(1), expected)) { return Fail("TH1D fill regression"); }
  }
  for (auto &[names, histogram] : handler->GetHistograms2D()) {
    const double expected = names.second.empty() ? 2 : names.second == "up" ? 6 : -3;
    if (!Close(histogram->GetBinContent(histogram->FindBin(0.5, 0.5)), expected)) {
      return Fail("TH2D fill regression");
    }
  }
  for (auto &[names, profile] : handler->GetProfiles2D()) {
    const double expected = names.second.empty() ? 58 : names.second == "up" ? 8 : 6;
    if (!Close(profile->GetBinContent(profile->FindBin(0.5, 0.5)), expected)) {
      return Fail("TProfile2D fill or variation reset regression");
    }
  }

  handler->SetEventWeights({{"default", 1.0F}, {"up", 1.0F}, {"down", 1.0F}});
  for (const auto &point : {std::vector<double>{-1, 0.5, 10.5},
                            {3, 0.5, 10.5},
                            {0.5, -2, 10.5},
                            {0.5, 3, 10.5},
                            {0.5, 0.5, 9},
                            {0.5, 0.5, 15}}) {
    handler->Fill("volume", point[0], point[1], point[2]);
    if (!Close(volume->GetBinContent(volume->FindBin(point[0], point[1], point[2])), 1)) {
      return Fail("TH3D underflow or overflow is incorrect");
    }
  }
  handler->SetEventWeights({{"default", 1.0F}, {"late", 2.0F}});
  if (handler->GetHistograms3D().size() != 11) { return Fail("Later weights unexpectedly created variations"); }
  std::ostringstream warnings;
  auto *previousOutput = std::cout.rdbuf(warnings.rdbuf());
  handler->Print();
  std::cout.rdbuf(previousOutput);
  if (warnings.str().find("Histogram defined but not filled: empty") == std::string::npos ||
      warnings.str().find("Histogram defined but not filled: volume") != std::string::npos ||
      warnings.str().find("Histogram defined but not filled: variable") != std::string::npos ||
      warnings.str().find("Histogram defined but not filled: unselected") != std::string::npos) {
    return Fail("TH3D unfilled-histogram bookkeeping is incorrect");
  }
  handler->SaveHistograms();
  TFile output(argv[2], "read");
  for (const auto &[names, histogram] : handler->GetHistograms3D()) {
    const std::string directory = names.first == "variable"                           ? "variable_volumes/"
                                  : names.first == "volume" || names.first == "empty" ? "volumes/"
                                                                                      : "";
    auto *saved = dynamic_cast<TH3D *>(output.Get((directory + histogram->GetName()).c_str()));
    if (!saved || saved->GetNcells() != histogram->GetNcells() ||
        !Close(saved->GetEntries(), histogram->GetEntries())) {
      return Fail("Persisted TH3D types, directories, binning or entries are incorrect");
    }
    for (int bin = 0; bin < saved->GetNcells(); ++bin) {
      if (!Close(saved->GetBinContent(bin), histogram->GetBinContent(bin)) ||
          !Close(saved->GetBinError(bin), histogram->GetBinError(bin))) {
        return Fail("Persisted TH3D content or errors are incorrect");
      }
    }
  }
  return 0;
}
