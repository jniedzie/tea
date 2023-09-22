#include "ConfigManager.hpp"
#include "CutFlowManager.hpp"
#include "Event.hpp"
#include "EventReader.hpp"
#include "EventWriter.hpp"
#include "ExtensionsHelpers.hpp"
#include "HistogramsHandler.hpp"
#include "Profiler.hpp"

// If you also created a histogram filler, you can include it here
// #include "MyHistogramsFiller.hpp"

using namespace std;

void CheckArgs(int argc, char **argv) {
  if (argc != 2) {
    fatal() << "Usage: " << argv[0] << " config_path\n";
    exit(1);
  }
}

int main(int argc, char **argv) {
  CheckArgs(argc, argv);

  // Pass the path to config file as an argument to the app
  string configPath = argv[1];
  auto config = make_unique<ConfigManager>(configPath);

  // Create event reader and writer, which will handle input/output trees for you
  auto eventReader = make_shared<EventReader>(configPath);
  auto eventWriter = make_shared<EventWriter>(configPath, eventReader);
  
  // Create a CutFlowManager to keep track of how many events passed selections
  auto cutFlowManager = make_shared<CutFlowManager>(eventReader, eventWriter);

  // If you want to fill some histograms, use HistogramsHandler to automatically create histograms
  // you need based on the config file, make them accessible to your HistogramFiller and save them at the end
  auto histogramsHandler = make_shared<HistogramsHandler>(configPath);
  histogramsHandler->SetupHistograms();

  // If you also created a HistogramFiller, construct it here to use it later on in the event loop
  // auto histogramsFiller = make_unique<MyHistogramsFiller>(configPath, histogramsHandler);

  // In case you're worried about the performance of your app, you can also create a profiler
  Profiler &profiler = Profiler::GetInstance();

  // You can also read any additional parameter from the config file
  int myParameter;
  config->GetValue("myParameter", myParameter);

  // You can use logger functionalities to print different types of messages
  info() << "Print some info" << endl;
  warn() << "Print some warning" << endl;
  error() << "Print some error" << endl;
  fatal() << "Print some fatal error" << endl;

  // In case you're worried about the performance and want to measure how much time different operations take,
  // simply surround them with Start/Stop calls to the profiler
  profiler.Start("my_first_measurement");
  sleep(10);  // perform some task
  profiler.Stop("my_first_measurement");

  profiler.Start("my_second_measurement");
  sleep(7);  // perform some task
  profiler.Stop("my_second_measurement");

  // Start the event loop
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    // Get the event
    auto event = eventReader->GetEvent(iEvent);

    // If you want to do something with one of the collections, extract it here and loop over it
    shared_ptr<PhysicsObjects> physicsObjects = event->GetCollection("Particle");
    for (auto physicsObject : *physicsObjects) {
      // If you also created your custom PhysicsObject class, you can convert the physics object to your object type
      // auto myPhysicsObject = asMyPhysicsObject(physicsObject);

      // do something with physicsObject (or myPhysicsObject)
      // ...
    }

    // If you want to fill some histograms with your HistogramFiller, you can pass the event to it
    // histogramsFiller->Fill(event);

    // You can apply some cuts on the event and update the cut flow
    cutFlowManager->UpdateCutFlow("initial");

    bool passesTrigger = event->Get("someTriggerName");
    if(!passesTrigger) continue;
    cutFlowManager->UpdateCutFlow("trigger");

    int nMuons = event->Get("nMuon");
    if(nMuons < 2) continue;
    cutFlowManager->UpdateCutFlow("nMuons");

    // If you want to store this event in the output tree, add it to the eventWriter
    eventWriter->AddCurrentEvent("Events");
  }

  // Tell histogram handler to store histograms
  histogramsHandler->SaveHistograms();

  // Tell CutFlowManager to save the cut flow
  cutFlowManager->SaveCutFlow();

  // Tell EventWriter to save the output tree
  eventWriter->Save();

  // Print results of time measurements
  profiler.Print();

  return 0;
}