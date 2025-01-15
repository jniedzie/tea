#include "ConfigManager.hpp"
#include "CutFlowManager.hpp"
#include "EventReader.hpp"
#include "EventWriter.hpp"
#include "ExtensionsHelpers.hpp"
#include "HistogramsHandler.hpp"
#include "Profiler.hpp"
#include "HistogramsFiller.hpp"
#include "ArgsManager.hpp"

// If you also created a histogram filler, you can include it here
// #include "MyHistogramsFiller.hpp"

using namespace std;

int main(int argc, char **argv) {
  
  auto args = make_unique<ArgsManager>(argc, argv);
  if (!args->GetString("config").has_value()) {
    fatal() << "No config file provided" << endl;
    exit(1);
  }

  ConfigManager::Initialize(args->GetString("config").value());
  auto &config = ConfigManager::GetInstance();
  
  if (args->GetString("input_path").has_value()) {
    config.SetInputPath(args->GetString("input_path").value());
  }
  if (args->GetString("output_hists_path").has_value()) {
    config.SetHistogramsOutputPath(args->GetString("output_hists_path").value());
  }
  if (args->GetString("output_trees_path").has_value()) {
    config.SetTreesOutputPath(args->GetString("output_trees_path").value());
  }

  // Create event reader and writer, which will handle input/output trees for you
  auto eventReader = make_shared<EventReader>();
  auto eventWriter = make_shared<EventWriter>(eventReader);
  
  // Create a CutFlowManager to keep track of how many events passed cuts
  auto cutFlowManager = make_shared<CutFlowManager>(eventReader, eventWriter);

  // If you want to fill some histograms, use HistogramsHandler to automatically create histograms
  // you need based on the config file, make them accessible to your HistogramFiller and save them at the end
  auto histogramsHandler = make_shared<HistogramsHandler>();
  
  // Create a HistogramFiller to fill default histograms
  auto histogramsFiller = make_unique<HistogramsFiller>(histogramsHandler);
  
  // If you also created your custom HistogramFiller, construct it here to use it later on in the event loop
  // auto histogramsFiller = make_unique<MyHistogramsFiller>(histogramsHandler);

  // In case you're worried about the performance of your app, you can also create a profiler
  Profiler &profiler = Profiler::GetInstance();

  // You can also read any additional parameter from the config file
  int myParameter;
  config.GetValue("myParameter", myParameter);

  // You can use logger functionalities to print different types of messages
  info() << "Print some info" << endl;
  warn() << "Print some warning" << endl;
  error() << "Print some error" << endl;
  fatal() << "Print some fatal error" << endl;

  // In case you're worried about the performance and want to measure how much time different operations take,
  // simply surround them with Start/Stop calls to the profiler
  profiler.Start("my_first_measurement");
  sleep(1);  // perform some task
  profiler.Stop("my_first_measurement");

  profiler.Start("my_second_measurement");
  sleep(2);  // perform some task
  profiler.Stop("my_second_measurement");

  cutFlowManager->RegisterCut("initial");
  cutFlowManager->RegisterCut("trigger");
  cutFlowManager->RegisterCut("nMuons");

  // Start the event loop
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    // Get the event
    auto event = eventReader->GetEvent(iEvent);

    // If you want to do something with one of the collections, extract it here and loop over it
    auto physicsObjects = event->GetCollection("Muon");
    for (auto physicsObject : *physicsObjects) {
      float pt = physicsObject->Get("pt");
      info() << "Physics object pt: " << pt << endl;
      // If you also created your custom PhysicsObject class, you can convert the physics object to your object type
      // auto myPhysicsObject = asMyPhysicsObject(physicsObject);

      // do something with physicsObject (or myPhysicsObject)
      // ...
    }

    // If you want to fill some histograms with your HistogramFiller, you can pass the event to it
    // histogramsFiller->Fill(event);

    // You can apply some cuts on the event and update the cut flow
    cutFlowManager->UpdateCutFlow("initial");

    bool passesTrigger = event->Get("HLT_IsoMu27");
    if(!passesTrigger) continue;
    cutFlowManager->UpdateCutFlow("trigger");

    int nMuons = event->GetCollection("Muon")->size();
    if(nMuons < 2) continue;
    cutFlowManager->UpdateCutFlow("nMuons");

    // If you want to store this event in the output tree, add it to the eventWriter
    eventWriter->AddCurrentEvent("Events");
  }

  // Tell histogram handler to store histograms
  histogramsHandler->SaveHistograms();

  // Tell CutFlowManager to save the cut flow
  cutFlowManager->SaveCutFlow();
  cutFlowManager->Print();

  // Tell EventWriter to save the output tree
  eventWriter->Save();

  // Print results of time measurements
  profiler.Print();

  // Print cumulative logs
  auto &logger = Logger::GetInstance();
  logger.Print();

  return 0;
}