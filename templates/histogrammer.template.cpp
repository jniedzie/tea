#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"
#include "HistogramsHandler.hpp"
#include "HistogramsFiller.hpp"

// If you also created a histogram filler, you can include it here
// #include "MyHistogramsFiller.hpp"

using namespace std;

void CheckArgs(int argc, char **argv) {
  if (argc != 2 && argc != 4) {
    fatal() << "Usage: " << argv[0] << " config_path"<<endl;
    fatal() << "or"<<endl;
    fatal() << argv[0] << " config_path input_path output_path"<<endl;
    exit(1);
  }
}

int main(int argc, char **argv) {
  CheckArgs(argc, argv);
  
  // Initialize ConfigManager with the path passed as an argument to the app
  ConfigManager::Initialize(argv[1]);

  // If you want to have an option to override input/output paths, do it here
  if(argc == 4){
    auto &config = ConfigManager::GetInstance();
    config.SetInputPath(argv[2]);
    config.SetOutputPath(argv[3]);
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
    // Get the event
    auto event = eventReader->GetEvent(iEvent);

    histogramsFiller->FillDefaultVariables(event);
    // If you have a custom histograms filler, use it to fill your custom histograms for this event
    // myHistogramsFiller->Fill(event);
  }

  // Tell histogram handler to save histograms
  histogramsHandler->SaveHistograms();
  return 0;
}