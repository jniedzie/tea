---
title: Adding event collections
permalink: /docs/event_collections/
redirect_from:
  - /docs/extra_event_collections/
---

`extraEventCollections` creates selected or combined collections without custom C++. A collection definition names one or more inputs and optional property requirements.

## Select one input collection

```python
extraEventCollections = {
  "TightMuons": {
    "inputCollections": ["Muon"],
    "pt": (30.0, 9999999.0),
    "eta": (-2.4, 2.4),
    "tightId": True,
  },
}
```

The event exposes `TightMuons` and its size as `nTightMuons`.

## Combine compatible collections

```python
extraEventCollections = {
  "LooseLeptons": {
    "inputCollections": ["Muon", "Electron"],
    "pt": (15.0, 9999999.0),
    "eta": (-2.4, 2.4),
  },
}
```

Only select on properties present with compatible types in every input collection.

## Use the collection

In C++:

```cpp
auto leptons = event->GetCollection("LooseLeptons");
```

In configuration:

```python
eventCuts = {
  "nLooseLeptons": (2, 9999999),
}
```

For behavior that requires calculations rather than property ranges, use [custom physics objects and events]({{ "/docs/custom_data_model/" | relative_url }}).
