---
title: Types in <code class="monospace">tea</code>
permalink: /docs/types_in_tea/
---

To understand how types are handled in `tea`, we recommend to first complete the [Custom printer app]({{site.baseurl}}/docs/custom_app_printer/) exercise. When you do it, you may notice something interesting: we get a `float` variable `“pt”` from the branch, but what if it was a different type, let’s say `int`?

---

## Let's break it

Well, let’s see what would happen if we changed `float` to `int` in this example:

```cpp
int pt = muon->Get("pt");
```

Recompile and run the example:

```bash
cd build
make -j install
cd ../bin
./ttZ_analysis_print_events ttZ_analysis_print_events_config.py
```

As you see, it actually compiled (which is rather unexpected), however it throws and exception when you try to run it.

---

## Multitype

The problem is that we don’t want to have different methods for different types, like `GetInt(...)`, `GetFloat(...)`, etc. Since C++ doesn’t allow overloading methods only based on return type, we use a little workaround:
- `Get(...)` returns a Schrödinger’s object that doesn’t know what type it is.
- When we assign it to a variable of a specific type, it calls the corresponding cast operator.
- The cast operator checks the actual branch type and either returns the value or throws an exception.

---

## Bottom line

You can access a variable of any type through `Get(...)`, but you have to know its type beforehand. Alternatively, you can use `GetAs<some_type>(...)` to cast it to another type, if you're sure you know what you're doing.
