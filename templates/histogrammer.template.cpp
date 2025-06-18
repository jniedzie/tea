#include "ArgsManager.hpp"
#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"
#include "HistogramsFiller.hpp"
#include "HistogramsHandler.hpp"

// If you also created a histogram filler, you can include it here
// #include "MyHistogramsFiller.hpp"

using namespace std;

int main(int argc, char **argv) {
  auto args = make_unique<ArgsManager>(argc, argv);

  // Initialize ConfigManager with the path passed as an argument to the app
  ConfigManager::Initialize(args->GetString("config").value());
  auto &config = ConfigManager::GetInstance();

  // If input path was provided as an argument, set it in the config.
  // Otherwise, it will be set to the value from the config file.
  if (args->GetString("input_path").has_value()) {
    config.SetInputPath(args->GetString("input_path").value());
  }
  if (args->GetString("output_hists_path").has_value()) {
    config.SetHistogramsOutputPath(args->GetString("output_hists_path").value());
  }

  // Create event reader and writer, which will handle input/output trees for you
  auto eventReader = make_shared<EventReader>();

  // If you want to fill some histograms, use HistogramsHandler to automatically create histograms
  // you need based on the config file, make them accessible to your HistogramFiller and save them at the end
  auto histogramsHandler = make_shared<HistogramsHandler>();

  // Create a HistogramFiller to fill default histograms
  auto histogramsFiller = make_unique<HistogramsFiller>(histogramsHandler);

  // If you have a custom histograms filler, create it here
  // auto myHistogramsFiller = make_unique<MyHistogramsFiller>(histogramsHandler);

  // Start the event loop
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);  // Get the event

    histogramsFiller->FillDefaultVariables(event);
    // If you have a custom histograms filler, use it to fill your custom histograms for this event
    // myHistogramsFiller->Fill(event);
  }

  // Tell histogram handler to save histograms
  histogramsHandler->SaveHistograms();
  return 0;
}