---
title: Custom events
permalink: /docs/custom_events/
---

Custom event classes let you add some special functionality on top of the event. Imagine you have a sample of events enriched in tt̄ process, so you would like to have an easy way to check if your event passes some criteria for hadronic or leptonic decay channels. You can create a custom event (see [Create apps & classes]({{site.baseurl}}/docs/create_script/) for details), for instance:

```bash
python tea/create.py --name TTEvent --type Event
```

Then, in your app you can simply convert an Event to a TTEvent (no need to implement the conversion, it will be added automatically) and call your custom method:

```cpp
auto ttEvent = asTTEvent(event);
bool isSemiLeptonic = ttEvent->IsSemiLeptonic();
```
