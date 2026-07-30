---
title: Reading and writing ROOT trees
nav_title: Reading ROOT trees
permalink: /docs/tree_io/
redirect_from:
  - /docs/tree_reader/
  - /docs/tree_writer/
---

`EventReader` and `EventWriter` form the ROOT tree I/O layer. Some users meet them through a built-in app, but custom applications can use them directly.

## Read events

After configuration is initialized, construct a reader and loop over its entries:

```cpp
auto eventReader = std::make_shared<EventReader>();

for (int iEvent = 0; iEvent < eventReader->GetNevents(); ++iEvent) {
  auto event = eventReader->GetEvent(iEvent);
  auto muons = event->GetCollection("Muon");
}
```

Important configuration fields include `inputFilePath`, `nEvents`, and `eventsTreeNames`.

## Write selected events

Create the writer from the same reader. Add the current entry only after it passes the selection:

```cpp
auto eventWriter = std::make_shared<EventWriter>(eventReader);

// Inside the event loop:
eventWriter->AddCurrentEvent("Events");

// After the loop:
eventWriter->Save();
```

Set `treeOutputFilePath` for the output and use `branchesToKeep` and `branchesToRemove` to control its branches. See [Pruning trees]({{ "/docs/pruning/" | relative_url }}).

## Branches and collections

For NanoAOD-style branches such as `Muon_pt` and `Muon_eta`, `event->GetCollection("Muon")` returns objects whose properties can be read with `Get("pt")` and `Get("eta")`. Event-level branches are available from the `Event` object. See the [event and collection API]({{ "/docs/event_api/" | relative_url }}) for the object model.
