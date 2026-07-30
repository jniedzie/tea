---
title: Type handling
permalink: /docs/types/
redirect_from:
  - /docs/types_in_tea/
---

ROOT branches can contain several scalar and vector types. `tea` uses `Multitype` so the same `Get` interface can return them without separate method names.

## Assignment performs the conversion

```cpp
float pt = muon->Get("pt");
int charge = muon->Get("charge");
```

`Get` returns a value wrapper; assigning it selects the requested cast. If the requested C++ type does not match the stored branch type, `tea` throws instead of silently converting.

## Determine the branch type

Inspect the input ROOT file rather than inferring a type from the variable name:

```bash
rootls -t sample.root
```

This matters for types such as `Float_t`, `Double_t`, signed and unsigned short integers, and their vector forms.

## Custom code

Use explicit types in app and extension code. When supporting a new ROOT type, update the central type-handling implementation and test both reading and assignment; do not work around a mismatch with an unrelated cast.
