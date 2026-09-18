#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
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
  if (argc != 3) { return Fail("Expected configuration and output paths"); }
  setenv("TEA_PROFILE2D_TEST_OUTPUT", argv[2], 1);
  ConfigManager::Initialize(argv[1]);

  auto handler = std::make_unique<HistogramsHandler>();
  auto *regular = handler->GetProfile2D({"response", ""});
  auto *variable = handler->GetProfile2D({"response_variable", ""});
  if (!regular || !variable) { return Fail("Nominal profiles were not created"); }
  if (regular->GetNbinsX() != 2 || regular->GetNbinsY() != 2) { return Fail("Regular binning is incorrect"); }
  if (!Close(variable->GetXaxis()->GetBinUpEdge(2), 3.0) || !Close(variable->GetYaxis()->GetBinUpEdge(2), 4.0)) {
    return Fail("Variable binning is incorrect");
  }

  handler->SetEventWeights({{"default", 2.0F}, {"up", 4.0F}});
  handler->Fill("response", 0.5, 0.5, 10.0);
  handler->Fill("response_variable", 2.0, 2.0, 6.0);
  handler->SetEventWeights({{"default", 1.0F}, {"up", 2.0F}});
  handler->Fill("response", 0.5, 0.5, 4.0);
  handler->Fill("response_variable", 2.0, 2.0, 3.0);

  const int regularBin = regular->FindBin(0.5, 0.5);
  if (!Close(regular->GetBinContent(regularBin), 8.0) || !Close(regular->GetBinEntries(regularBin), 3.0)) {
    return Fail("Nominal profile did not apply event weights");
  }
  auto *regularUp = handler->GetProfile2D({"response", "up"});
  if (!regularUp || !Close(regularUp->GetBinContent(regularBin), 8.0) ||
      !Close(regularUp->GetBinEntries(regularBin), 6.0)) {
    return Fail("Scale-factor variation profile is incorrect");
  }
  const int variableBin = variable->FindBin(2.0, 2.0);
  auto *variableUp = handler->GetProfile2D({"response_variable", "up"});
  if (!Close(variable->GetBinContent(variableBin), 5.0) || !variableUp ||
      !Close(variableUp->GetBinContent(variableBin), 5.0)) {
    return Fail("Variable-bin profile contents are incorrect");
  }
  if (handler->GetProfiles2D().size() != 4) { return Fail("Profile getter returned an unexpected object count"); }

  handler->SaveHistograms();
  TFile output(argv[2], "read");
  auto *savedRegular = dynamic_cast<TProfile2D *>(output.Get("profiles/response"));
  auto *savedVariation = dynamic_cast<TProfile2D *>(output.Get("profiles/response_up"));
  auto *savedVariable = dynamic_cast<TProfile2D *>(output.Get("variable_profiles/response_variable"));
  if (!savedRegular || !savedVariation || !savedVariable) {
    return Fail("Persisted profile types or directories are incorrect");
  }
  if (!Close(savedRegular->GetBinContent(regularBin), 8.0) || !Close(savedVariable->GetBinContent(variableBin), 5.0)) {
    return Fail("Persisted profile content is incorrect");
  }
  return 0;
}
