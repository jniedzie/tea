---
title: Adding physics objects and events
nav_title: Physics objects and events
permalink: /docs/custom_data_model/
redirect_from:
  - /docs/custom_physics_objects/
  - /docs/custom_events/
---

Custom physics objects add behavior to one object; custom events add behavior that depends on the whole event. Both live in `libs/user_extensions/` and are generated with conversion helpers.

## Add a physics object

```bash
python3 tea/create.py --type PhysicsObject --name TopQuark
```

Implement behavior in the generated header and source, then convert a generic object:

```cpp
auto topQuark = asTopQuark(physicsObject);
bool boosted = topQuark->IsBoosted();
```

Use this for object-level identification, derived properties, or relationships that belong to one physics object.

## Add an event

```bash
python3 tea/create.py --type Event --name TTEvent
```

Convert inside the application:

```cpp
auto ttEvent = asTTEvent(event);
bool semileptonic = ttEvent->IsSemiLeptonic();
```

Use an event class for event categories, candidate selection across collections, or other event-wide behavior.

## Rebuild and test

```bash
source tea/build.sh
```

Test conversion of null and populated objects, input-branch types, and the domain logic. Generated casts reduce boilerplate but do not validate the physics assumptions.
