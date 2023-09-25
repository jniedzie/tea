#include "TemplateName.hpp"

#include "ConfigManager.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

TemplateName::TemplateName(string configPath, shared_ptr<HistogramsHandler> histogramsHandler_)
    : histogramsHandler(histogramsHandler_) {
  auto configManager = make_unique<ConfigManager>(configPath);

  // Here you can get some parameters from the config file
  // map<string, vector<string>> triggerSets;
  // configManager->GetMap("triggerSets", triggerSets);

  eventProcessor = make_unique<EventProcessor>();
}

TemplateName::~TemplateName() {}


void TemplateName::Fill(const std::shared_ptr<Event> event) {
  // verify that the histogram exists
  string histName = "test";
  histogramsHandler->CheckHistogram(histName);

  // Fill the histogram for given event (e.g. use EventProcessor to get some variables)
  histogramsHandler->histograms1D[histName]->Fill(eventProcessor->GetMaxPt(event, "Muon"));
}