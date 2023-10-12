---
title: Example apps
permalink: /docs/example_app/
---

---
## Printing variables from a tree

Imagine a scenario in which you have a ROOT tree with branches such as "Muon_pt", "Muon_eta", "Electron_pt", "Electron_eta", etc. You want to print transverse momentum of all muons in all events. In `tea`, you would use `EventReader` class, so your app could look like this:

```cpp
#include "ConfigManager.hpp"
#include "EventReader.hpp"

int main() {
  ConfigManager::Initialize("config.py");
  auto eventReader = make_shared<EventReader>();
  
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);

    auto muons = event->GetCollection("Muon");
    for (auto muon : *muons) {
      float pt = muon->Get("pt");
      info() << pt << std::endl;
    }
  }
  return 0;
}
```

With the `config.py` file simply containing the path to the input file and number of events to run on (where "-1" means to include all events):

```python
inputFilePath = "../samples/background_dy.root"
nEvents = -1
```

---
## Creating histograms

Now, imagine you want to store transverse momenta of all muons in all events in a histogram. `tea` makes it easy with its `HistogramsHandler` and `HistogramsFiller` classes:

```cpp
#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "HistogramsHandler.hpp"
#include "HistogramsFiller.hpp"

int main() {
  ConfigManager::Initialize("config.py");
  auto eventReader = make_shared<EventReader>();
  
  auto histogramsHandler = make_shared<HistogramsHandler>();
  auto histogramsFiller = make_unique<HistogramsFiller>(histogramsHandler);

  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);
    histogramsFiller->FillDefaultVariables(event);
  }
  histogramsHandler->SaveHistograms();
  return 0;
}
```

With the actual histograms to store defined in the `config.py` file:

```python
inputFilePath = "../samples/background_dy.root"
nEvents = -1

histogramsOutputFilePath = "../samples/histograms/background_dy.root"

defaultHistParams = (
#  collection      variable          bins    xmin     xmax     dir
  ("Muon"        , "pt"            , 400,    0,       200,     ""  ),
)
```

---

## Skimming

Finally, let's consider a scenario in which you only want to keep events which contain at least two muons. Saving passing events to a tree can be easily achieved with the `EventWriter` class:

```cpp
#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "EventWriter.hpp"

int main() {
  ConfigManager::Initialize("config.py");
  auto eventReader = make_shared<EventReader>();
  auto eventWriter = make_shared<EventWriter>(eventReader);

  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);

    if(event->GetCollectionSize("Muon") < 2) continue;
    eventWriter->AddCurrentEvent("Events");
  }
  eventWriter->Save();
  return 0;
}
```

With the cut on number of muons defined in the `config.py` file:

```python
inputFilePath = "../samples/background_dy.root"
treeOutputFilePath = "../samples/skim/background_dy.root"
nEvents = -1

eventSelections = {
    "nMuon": (2, 9999999),
}
```