#include "ConfigManager.hpp"
#include "Event.hpp"
#include "EventReader.hpp"
#include "HistogramsFiller.hpp"
#include "HistogramsHandler.hpp"
#include "CutFlowManager.hpp"

using namespace std;

int main(int argc, char **argv) {
  if (argc != 2) {
    fatal() << "Usage: " << argv[0] << " config_path\n";
    exit(1);
  }

  string configPath = argv[1];

  auto eventReader = make_shared<EventReader>(configPath);
  auto histogramsHandler = make_shared<HistogramsHandler>(configPath);
  auto cutFlowManager = make_shared<CutFlowManager>(eventReader);
  auto histogramsFiller = make_unique<HistogramsFiller>(configPath, histogramsHandler);

  histogramsHandler->SetupHistograms();

  for (int i_event = 0; i_event < eventReader->GetNevents(); i_event++) {
    auto event = eventReader->GetEvent(i_event);

    histogramsFiller->FillDefaultVariables(event);
  }
  
  histogramsFiller->FillCutFlow(cutFlowManager);

  histogramsHandler->SaveHistograms();

  return 0;
}