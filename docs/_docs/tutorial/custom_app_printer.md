---
title: Custom printer app
permalink: /docs/custom_app_printer/
---

The goal of this exercise is to create an app which prints values of some branches from the input tree. In our case, we will try to print transverse momenta ("pt" variable) of all muons ("Muon" collection) from an example `background_dy.root` file.

---

## Create a new app

Please refer to [Create apps & classes]({{site.baseurl}}/docs/create_script/) page for detailed explanation on how we create things in `tea`. For this excercise, we will create a printer:

```bash
python tea/create.py --name ttZ_analysis_print_events --type printer
```

---

## Modify the app

Open the `ttZ_analysis_print_events.cpp` file created in the previous step. Have a look at its contents and try to figure out how to print transverse momenta of muons. Below you can find an example of a complete app:

```cpp
#include "ArgsManager.hpp"
#include "ConfigManager.hpp"
#include "EventReader.hpp"
#include "ExtensionsHelpers.hpp"

using namespace std;

int main(int argc, char **argv) {
  auto args = make_unique<ArgsManager>(argc, argv);

  ConfigManager::Initialize(args->GetString("config").value());
  auto &config = ConfigManager::GetInstance();

  auto eventReader = make_shared<EventReader>();

  for (int iEvent = 0; iEvent < eventReader->GetNevents(); iEvent++) {    
    auto event = eventReader->GetEvent(iEvent);
    auto physicsObjects = event->GetCollection("Muon");

    for (auto physicsObject : *physicsObjects) {
      float pt = physicsObject->Get("pt");
      info() << "Physics object pt: " << pt << endl;
    }
  }

  return 0;
}
```

---

## Modify the config

Next, we need to modify the config file (name ending with `_config.py`). Specify the input path and the number of events to run on:

```python
inputFilePath = "../tea/samples/background_dy.root"

nEvents = 5
printEveryNevents = 1
```

---

## Build & run

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
Physics object pt: 7.64029
Event: 2
Physics object pt: 30.4176
Event: 3
Physics object pt: 24.5016
Physics object pt: 24.4605
Event: 4
Physics object pt: 14.7816
Physics object pt: 6.56101
```
