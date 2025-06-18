---
title: HEPMC support
permalink: /docs/hepmc/
---

For pheno studies, we often use HepMC objects that represent gen-level particles. There are two classes in `tea` that will help you handle them:

- `HepMCParticle`: Represents a particle and gives easy access to its properties. It also makes it easy to find particles mother and daughters.

- `HepMCProcessor`: Provides some additional functionality, such as checking if given particle is the last copy, or finding a common mother of two particles.

If you're missing some HepMC functionality - feel free to contribute by creating a PR, or create an [issue in GitHub](https://github.com/jniedzie/tea/issues)!
