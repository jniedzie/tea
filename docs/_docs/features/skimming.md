---
title: Skimming
permalink: /docs/skimming/
---

Skimming is a process in which we drop some uninteresting events from the ROOT trees. This page explains how to perform basic or advanced skimming with `tea`.

---

## Basic skimming

Simple skimming can be achieved directly from the config file - you can apply basic cuts on event properties. There are two variables that control it - `triggerSelection` and `eventCuts`:

```python
triggerSelection = (
    "HLT_IsoMu24",
)

eventCuts = {
    "MET_pt": (30, 9999999),
    "nMuon": (1, 9999999),
    "nGoodLeptons": (1, 9999999),
}
```

In the `eventCuts` you are also allowed to use your `extraEventCollections` - check out the [tutorial page]({{site.baseurl}}/docs/extra_event_collections/) to learn more about it.

If you want to do simple skimming, have a look at [My first skimmer]({{site.baseurl}}/docs/my_first_skimming/) tutorial.

---

## Advanced skimming

Sometimes using existing branches and extra collections is not enough. In this case you will need to write a dedicated skimmer app. Fortunately, you don't have to start from scratch - use [create.py]({{site.baseurl}}/docs/create_script/) script to create and app. This will create a skeleton for you that contains a baseline for your custom skimmer, giving you the full freedom of accessing any default and extra collections, performing any operations/selections you want, and saving surviving events to the output file.

If you're into custom skimming, you may also be interested in [custom physics objects]({{site.baseurl}}/docs/custom_physics_objects/) and [custom events]({{site.baseurl}}/docs/custom_events/) that will make your code cleaner and will help you organize your skimming app.
