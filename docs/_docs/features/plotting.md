---
title: Plotting
permalink: /docs/plotting/
---

Plotting is handled by `plotter.py` script, which takes your config as an input. It will automatically handle stacking backgrounds, calculating their uncertainty, calculating data-MC ratios, normalizing (there are several options), and applying consistent style.

This can quickly become rather complicated, which is why we recommend to start from a [simple tutorial]({{site.baseurl}}/docs/my_first_plots/). Once you understand the basics, you may want to have a look at a more [complete config](https://github.com/jniedzie/tea/blob/main/configs/examples/plotter_config.py) file, demonstrating plotting of many histograms for multiple background, signal, and data samples

In your analysis, this config will probably grow even more - remember that you're free to split it into smaller files and include your helpers in the main plotting config. Some lists/dicts can also be generated programatically - the config will be properly executed, so you're free to do whatever you want there.

If you find any bugs, missing features, or you want to make plotting better - feel free to contribute by creating a PR, or create an [issue in GitHub](https://github.com/jniedzie/tea/issues)!