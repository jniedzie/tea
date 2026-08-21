#include "ExtensionsHelpers.hpp"
#include "TemplateName.hpp"

using namespace std;

TemplateName::TemplateName(shared_ptr<HistogramsHandler> histogramsHandler_) : histogramsHandler(histogramsHandler_) {
  // Create a config manager
  auto &config = ConfigManager::GetInstance();
  eventProcessor = make_unique<EventProcessor>();
}

TemplateName::~TemplateName() {}

void TemplateName::Fill(const std::shared_ptr<Event> event) {
  // Fill the histogram for given event (e.g. use EventProcessor to get some variables)
  histogramsHandler->Fill("test", eventProcessor->GetMaxPt(event, "Muon"));
}
