//  histogramming_test.cpp
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

  auto muonPt = new TH1D("muonPt", "muonPt", 100, 0, 100);
  auto muonEta = new TH1D("muonEta", "muonEta", 100, -5, 5);

  for (int iEvent = 0; iEvent < 1000; iEvent++) {
    auto event = eventReader->GetEvent(iEvent);
    // auto ttAlpsEvent = asTTAlpsEvent(event);
    // info() << ttAlpsEvent->GetTTbarEventCategory() << endl;

    auto muons = event->GetCollection("Muon");

    for(auto muon : *muons){
      muonPt->Fill(muon->Get("pt"));
      muonEta->Fill(muon->Get("eta"));
    }
    // auto physicsObjects = event->GetCollection("GenPart");

    // for (auto physicsObject : *physicsObjects) {
    //   auto genParticle = asGenParticle(physicsObject);

    //   int pdgId = genParticle->Get("pdgId");
    //   cout << "pid: " << genParticle->GetPdgId() << endl;
    //   genParticle->print();
    // }
  }

  auto outputFile = new TFile("hists.root", "recreate");
  outputFile->cd();

  muonPt->Write();
  muonEta->Write();

  outputFile->Close();

  return 0;
}