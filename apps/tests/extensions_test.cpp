//  extensions_test.cpp
//
//  Created by Jeremi Niedziela on 08/08/2023.

#include "EventProcessor.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"
#include "GenParticle.hpp"
#include "Helpers.hpp"

using namespace std;

int main() {
  string inputPath =
      "/Users/jeremi/Documents/Physics/DESY/ttalps_cms.nosync/data/backgrounds/"
      "TTbar_inclusive/FCA55055-C8F3-C44B-8DCC-6DCBC0B8B992.root";

  auto eventReader = make_shared<EventReader>(inputPath);
  info() << "Event reader created" << endl;

  auto eventProcessor = make_unique<EventProcessor>();

  for (int iEvent = 0; iEvent < 10; iEvent++) {
    auto event = eventReader->GetEvent(iEvent);

    // auto ttAlpsEvent = asTTAlpsEvent(event);

    // info() << ttAlpsEvent->GetTTbarEventCategory() << endl;

    // auto physicsObjects = event->GetCollection("GenPart");

    // for (auto physicsObject : *physicsObjects) {
    //   auto genParticle = asGenParticle(physicsObject);

    //   int pdgId = genParticle->Get("pdgId");
    //   cout << "pid: " << genParticle->GetPdgId() << endl;
    //   genParticle->print();
    // }
  }

  return 0;
}