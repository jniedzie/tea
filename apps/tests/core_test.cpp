
#include "EventReader.hpp"
#include "EventWriter.hpp"
#include "Helpers.hpp"

using namespace std;

bool showBadExamples = true;
bool showFatallyBadExamples = false;

void printEventInto(const shared_ptr<Event> event) {
  if (showBadExamples) {
    // accessing a branch that doesn't exist
    double eventNumberBad = event->Get("events");

    // casting to a wrong type
    float runNumberBad = event->Get("run");
  }

  ULong64_t eventNumber = event->Get("event");
  uint runNumber = event->Get("run");
  bool hltFlag = event->Get("HLT_Mu8_IP3_part4");

  cout << "Event " << eventNumber << " from run: " << runNumber
       << " has the HLT flag: " << hltFlag << endl;
}

void printGenParticlesInfo(const shared_ptr<Event> event) {
  // get a collection and its size
  uint nGenParticles = event->Get("nGenPart");
  int maxParticles = nGenParticles > 10 ? 10 : nGenParticles;
  auto genParticles = event->GetCollection("GenPart");

  for (auto particle : *genParticles) {
    // use some element-level info
    int pdgId = particle->Get("pdgId");
    float pt = particle->Get("pt");
    cout << "\tParticle (" << pdgId << ") pt: " << pt << endl;
  }
}

void printMuonsInfo(const shared_ptr<Event> event) {
  if (showFatallyBadExamples) {
    // accessing collection that doesn't exist
    auto muonsBad = event->GetCollection("Muons");
  }

  auto muons = event->GetCollection("Muon");

  for (auto muon : *muons) {
    float pt = muon->Get("pt");
    if (showBadExamples) {
      // casting to a wrong type
      bool ptBad = muon->Get("pt");
    }
    cout << "\tMuon pt: " << pt << endl;
  }
}

int main() {
  string inputPath =
      "/Users/jeremi/Documents/Physics/DESY/ttalps_cms.nosync/data/backgrounds/"
      "TTbar_inclusive/FCA55055-C8F3-C44B-8DCC-6DCBC0B8B992.root";
  string outputPath = "test.root";

  auto eventReader = make_shared<EventReader>(inputPath);
  auto eventWriter = make_unique<EventWriter>(outputPath, eventReader);

  // auto nEvents = eventReader->GetNevents();

  for (int iEvent = 0; iEvent < 10; iEvent++) {
    auto event = eventReader->GetEvent(iEvent);

    uint nMuons = event->Get("nMuon");
    if (nMuons < 1) continue;

    printEventInto(event);
    printGenParticlesInfo(event);
    printMuonsInfo(event);

    eventWriter->AddCurrentEvent("Events");
  }

  eventWriter->Save();

  return 0;
}