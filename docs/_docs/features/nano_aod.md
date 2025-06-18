---
title: nanoAOD support
permalink: /docs/nano_aod/
---

The framework implements some convenience features to handle CMS nanoAOD samples. You can find the following clases in [`tea/libs/extensions`](https://github.com/jniedzie/tea/tree/main/libs/extensions/include):


- [`NanoEvent`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoEvent.hpp): provides a number of methods allowing easier access to MET, and otherwise facilitating operations on prompt and displaced muons, as well as dimuon vertices. 

- [`NanoEventProcessor`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoEventProcessor.hpp): gives access to event-level scale factors, tell you if a given event is data or MC, etc.

- [`NanoGenParticle`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoGenParticle.hpp): useful whenever you need to do some gen-level study/matching. It can give you the first copy of the gen particle, its kinematic properties, check if it is a given type of a particle, etc.

- [`NanoMuon`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoMuon.hpp), [`NanoElectron`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoElectron.hpp), [`NanoJet`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoJet.hpp): wrappers on top of reconstructed muons, electrons, and jets. Give access to object-level scale factors and some additional functionality (such as getting the gen-level muon assiociated with a reconstructed muon).

- [`NanoDimuonVertex`](https://github.com/jniedzie/tea/blob/main/libs/extensions/include/NanoDimuonVertex.hpp): if you're using LLPnanoAOD or EXOnanoAOD, this class will help with dimuon vertices handling.

If your object or a functionality is not covered yet - feel free to contribute by creating a PR, or create an [issue in GitHub](https://github.com/jniedzie/tea/issues)!
