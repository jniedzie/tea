---
title: Build the project
permalink: /docs/build/
---

Building TEA together with your analysis files is very straighforward:

```
mkdir build
cd build
cmake ..
make -j install
```

Once compiled, you can execute any of the apps directly from the `bin` directory (all configs will also be installed in this directory), e.g. `./skimmer skimmer_config.py`.