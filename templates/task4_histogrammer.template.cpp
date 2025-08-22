#include "ArgsManager.hpp"
#include "ConfigManager.hpp"
#include "EventProcessor.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"
#include "HistogramsHandler.hpp"
#include "HistogramsFiller.hpp"

using namespace std;

void FillHistograms(const shared_ptr<Event> &event, shared_ptr<HistogramsHandler> &histogramsHandler) {
  
  // A generic event can be converted to a NanoEvent, which represents an event in the nanoAOD format.
  // It will provide us with some additional functionality, making out life much easier.
  auto nanoEvent = asNanoEvent(event);

  // For instance, NanoEvent can return the best dimuon candidate in the event.
  auto bestDimuon = nanoEvent->GetBestDimuonVertex();

  // Then, we can simply fill the histograms with the properties of the best dimuon.
  // The histogram name must match the name defined in the config.
  histogramsHandler->Fill("Dimuon_minv", bestDimuon->GetInvariantMass());
}

int main(int argc, char **argv) {
  // ArgsManager helps to handle input parameters
  auto args = make_unique<ArgsManager>(argc, argv);

  // Config manager is our proxy to the python config
  ConfigManager::Initialize(args->GetString("config").value());
  auto &config = ConfigManager::GetInstance();

  if (args->GetString("input_path").has_value()) {
    config.SetInputPath(args->GetString("input_path").value());
  }
  if (args->GetString("output_hists_path").has_value()) {
    config.SetHistogramsOutputPath(args->GetString("output_hists_path").value());
  }

  // Here we initialize a few objects that will help us read events, keep track of cuts, and fill histograms
  auto eventReader = make_shared<EventReader>();
  auto eventProcessor = make_unique<EventProcessor>();
  auto cutFlowManager = make_shared<CutFlowManager>(eventReader);
  auto histogramsHandler = make_shared<HistogramsHandler>();
  auto histogramsFiller = make_unique<HistogramsFiller>(histogramsHandler);
  eventProcessor->RegisterCuts(cutFlowManager);

  // Start the event loop (the number of events is defined in the config)
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    
    // Get current event
    auto event = eventReader->GetEvent(iEvent);

    // Check if the event passes the basic selection criteria defined in the config
    if (!eventProcessor->PassesEventCuts(event, cutFlowManager)) continue;
    
    // If the event passed, let's fill the histograms
    FillHistograms(event, histogramsHandler);
  }

  // After the event loop, let's fill the cut flow histograms and save the output
  histogramsFiller->FillCutFlow(cutFlowManager);
  histogramsHandler->SaveHistograms();
  
  // Finally, let's print the cut flow and the summary of logs
  cutFlowManager->Print();
  Logger::GetInstance().Print();

  return 0;
}