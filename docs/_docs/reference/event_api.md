---
title: Event and collection API
permalink: /docs/event_api/
---

`EventReader` produces an `Event`. An event exposes event-level branches and named `Collection` objects, whose entries are `PhysicsObject` instances.

## Events

```cpp
auto event = eventReader->GetEvent(iEvent);
auto met = event->Get("MET_pt");
auto muons = event->GetCollection("Muon");
```

Use the concrete C++ type expected by the branch when assigning a value returned through `Multitype`.

## Collections and objects

```cpp
for (const auto &muon : *muons) {
  float pt = muon->Get("pt");
  float eta = muon->Get("eta");
}
```

The collection name is removed from object property names: `Muon_pt` becomes property `pt` in collection `Muon`.

## Extension helpers

`ExtensionsHelpers.hpp` provides conversions such as `asNanoEvent`. User-generated conversions are added to `libs/user_extensions/include/UserExtensionsHelpers.hpp`.

For exact signatures, inspect the current headers in `tea/libs/core/include/` and `tea/libs/extensions/include/`; this page describes the stable object model rather than duplicating every method.
