#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"

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

  // If you want to override input/output paths, you can do it here  
  if(argc == 4){
    auto &config = ConfigManager::GetInstance();
    config.SetInputPath(argv[2]);
    config.SetOutputPath(argv[3]);
  }

  // Create event reader and writer, which will handle input/output trees for you
  auto eventReader = make_shared<EventReader>();

  // Start the event loop
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    // Get the event
    auto event = eventReader->GetEvent(iEvent);

    // Extract a collection from the event
    auto physicsObjects = event->GetCollection("Particle");

    // Loop over the collection
    for (auto physicsObject : *physicsObjects) {
      // Get a branch value using its name
      float pt = physicsObject->Get("pt");

      // Use into(), warn(), error() and fatal() to print messages
      info() << "Physics object pt: " << pt << endl;
    }
  }

  return 0;
}