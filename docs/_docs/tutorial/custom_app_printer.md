---
title: Custom printer app
permalink: /docs/custom_app_printer/
---

The goal of this exercise is to create an app which prints values of some branches from the input tree. In our case, we will try to print transverse momenta ("pt" variable) of all muons ("Muon" collection) from an example `background_dy.root` file.

## Create a new app

Please refer to [create.py script]({{site.baseurl}}/docs/create_script/) page for detailed explanation on how we create things in `tea`. For this excercise, we will create a printer:

```bash
python tea/create.py --name ttZ_analysis_print_events --type printer
```

## Modify the app

Open the `ttZ_analysis_print_events.cpp` file created in the previous step. Have a look at its contents and try to figure out how to print transverse momenta of muons. Below you can find an example of a complete app:

```cpp
#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"


int main(int argc, char **argv) {
  ConfigManager::Initialize(argv[1]);
  auto eventReader = std::make_shared<EventReader>();
 
  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {
    auto event = eventReader->GetEvent(iEvent);
    auto muons = event->GetCollection("Muon");

    for (auto muon : *muons) {
      float pt = muon->Get("pt");
      info() << "Muon pt: " << pt << std::endl;
    }
  }
  return 0;
}
```

## Modify the config

Next, we need to modify the config file (name ending with `_config.py`). Specify the input path and the number of events to run on:

```python
inputFilePath = "../tea/samples/background_dy.root"

nEvents = 5
printEveryNevents = 1
```

## Build and run

Finally, build the project and run the app, specifying the corresponding config file:

```bash
source build.sh
cd bin
./ttZ_analysis_print_events ttZ_analysis_print_events_config.py
```

You would expect to see the following output:

```
Event: 0
Event: 1
Muon pt: 7.64029
Event: 2
Muon pt: 30.4176
Event: 3
Muon pt: 24.5016
Muon pt: 24.4605
Event: 4
Muon pt: 14.7816
Muon pt: 6.56101
```
