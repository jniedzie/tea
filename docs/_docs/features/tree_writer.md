---
title: Events writer
permalink: /docs/tree_writer/
---

## Class description

Trees can also be stored after some operations (e.g. skimming), which is handled by `EventWriter`. When you create it, it needs to know who is reading the trees, which is why you need to provide it with the `EventReader` object:

```cpp
auto eventWriter = make_shared<EventWriter>(eventReader);
```

It only has two public methods to add the current event to the output tree, and to save the output tree:

```cpp
eventWriter->AddCurrentEvent("Events");  // Add current event to a tree called "Events"
eventWriter->Save();  // Save output tree
```

---

## Related config options

There are a few options in the config that the `EventWriter` uses:

- `treeOutputFilePath`: path to the output file in which the trees will be stored.

- `branchesToKeep` and `branchesToRemove`: used for pruning, see the [related docs]({{site.baseurl}}/docs/pruning/).