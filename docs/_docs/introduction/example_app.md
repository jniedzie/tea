---
title: Example apps
permalink: /docs/example_app/
---

Have a look at these examples to get a general feel for what `tea` apps and configs look like. To actually learn step by step about different topics, such as skimming, histogramming, plotting, etc., go to tutorial pages on the left.

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

In reality, you wouldn't even have to write this app - it already exists and is called `histogrammer`. The only thinig you would need to provide is the config file.

---

## Skimming

Finally, let's consider a scenario in which you only want to keep events which contain at least two muons. While you could write your custom app to handle this task, it is so simple that you can also use the existing `skimmer` app and provide a simple config:

```python
inputFilePath = "../samples/background_dy.root"
treeOutputFilePath = "../samples/skim/background_dy.root"
nEvents = -1

eventSelections = {
    "nMuon": (2, 9999999),
}
```
