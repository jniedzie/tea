---
title: Events reader
permalink: /docs/tree_reader/
---

## Class description

Reading events from root trees is handled by `EventReader`. The class itself has a trivial constructor, so you create it without any arguments:

```cpp
auto eventReader = make_shared<EventReader>();
```

It only has two public methods, which return number of events in the tree, and the i-th event:

```cpp
eventReader->GetNevents()  // returns number of events
eventReader->GetEvent(7); // returns 7th event
```

---

## Related config options

Most of the functionality of `EventReader` is linked to options in the config file. Let's looks at the most important ones:

- `nEvents`: number of events to process (-1 means: all).

- `printEveryNevents`: print event number every N events.

- `inputFilePath`: path to the input ROOT file.

- `eventsTreeNames`: a list with the names of trees containing events. If not specified, one tree called `Events` will be assumed. You can specify some custom tree name, but currently providing more than one tree has no real effect - only the first element in this list matters.

- `specialBranchSizes`: if you have a collection whos size is stored in another branch, and its name cannot be easily deduced (i.e. for collection called "Collection" the size branch is not "nCollection"), you should specify here which branch to use to determine the size of this collection. If your collections are standard vectors, you don't need to do anything. 

- `redirector`: when accessing remote files, by default these three redirectors will be tried (in this order): "xrootd-cms.infn.it",
        "cms-xrd-global.cern.ch", and "cmsxrootd.fnal.gov". If you want to use a different redirector, set it in the config and it will be tried first.

