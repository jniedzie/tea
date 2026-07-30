---
title: Writing a custom app
permalink: /docs/custom_app/
redirect_from:
  - /docs/create_script/
  - /docs/custom_app_printer/
  - /docs/example_app/
---

Use a custom C++ app when configuration-only selection or histogramming cannot express the analysis. `tea/create.py` creates a skeleton in the analysis repository and updates the CMake cache state.

## Create an app

Run from the analysis root:

```bash
python3 tea/create.py --type app --name my_analysis
```

Available app templates are:

- `app`: general event loop;
- `printer`: event loop intended for inspection;
- `histogrammer`: event loop with histogram helpers;
- `task4_histogrammer`: the DAS LLP tutorial template.

The command creates `apps/my_analysis.cpp` and `configs/my_analysis_config.py`.

## Read configuration and events

A typical app parses `--config`, initializes `ConfigManager`, then reads events:

```cpp
auto args = std::make_unique<ArgsManager>(argc, argv);
ConfigManager::Initialize(args->GetString("config").value());

auto eventReader = std::make_shared<EventReader>();
for (int iEvent = 0; iEvent < eventReader->GetNevents(); ++iEvent) {
  auto event = eventReader->GetEvent(iEvent);
  // Analysis logic
}
```

Use the current generated template as the source of truth for constructor signatures; they evolve with the framework.

## Build and run

```bash
source tea/build.sh
cd bin
./my_analysis --config my_analysis_config.py
```

Keep reusable domain behavior in a custom object or event class rather than growing one application indefinitely.
