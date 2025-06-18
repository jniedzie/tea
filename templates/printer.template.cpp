#include "ArgsManager.hpp"
#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"

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

  // Create event reader and writer, which will handle input/output trees for you
  auto eventReader = make_shared<EventReader>();

  // Start the event loop
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    
    auto event = eventReader->GetEvent(iEvent); // Get the event
    auto physicsObjects = event->GetCollection("Particle"); // Extract a collection from the event

    // Loop over the collection
    for (auto physicsObject : *physicsObjects) {
      float pt = physicsObject->Get("pt");  // Get a branch value using its name

      // Use into(), warn(), error() and fatal() to print messages
      info() << "Physics object pt: " << pt << endl;
    }
  }

  return 0;
}