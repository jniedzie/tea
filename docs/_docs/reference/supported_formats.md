---
title: NanoAOD and HepMC support
nav_title: NanoAOD and HepMC
permalink: /docs/supported_formats/
redirect_from:
  - /docs/nano_aod/
  - /docs/hepmc/
---

`tea` reads flat ROOT trees. Its extension library adds convenience classes for CMS NanoAOD-style inputs and generator-level HepMC content converted to ROOT.

## NanoAOD

Available wrappers include:

- `NanoEvent` and `NanoEventProcessor` for event-level helpers;
- `NanoMuon`, `NanoElectron`, and `NanoJet` for reconstructed objects;
- `NanoGenParticle` for generator ancestry and matching;
- `NanoDimuonVertex` for LLPNanoAOD or EXONanoAOD dimuon vertices.

Convert only when the input actually follows the expected branches:

```cpp
auto nanoEvent = asNanoEvent(event);
```

## HepMC-derived ROOT trees

`HepMCParticle` represents generator particles and their relations. `HepMCProcessor` adds helpers such as last-copy checks and common-mother searches. `hepmc2root` is a specialized example application for conversion.

## Verify the schema

Format labels do not replace schema inspection. Check tree names, branch names, branch types, and collection-size conventions in the exact input production before selecting an extension class.
