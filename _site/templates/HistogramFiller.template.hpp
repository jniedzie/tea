#ifndef TemplateName_hpp
#define TemplateName_hpp

#include "Event.hpp"
#include "EventProcessor.hpp"
#include "Helpers.hpp"
#include "HistogramsHandler.hpp"

class TemplateName {
 public:
  TemplateName(std::string configPath, std::shared_ptr<HistogramsHandler> histogramsHandler_);
  ~TemplateName();

  void Fill(const std::shared_ptr<Event> event);

 private:
  std::shared_ptr<HistogramsHandler> histogramsHandler;
  std::unique_ptr<EventProcessor> eventProcessor;
};

#endif /* TemplateName_hpp */
