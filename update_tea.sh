#!/bin/bash

# update tea
git submodule update --remote tea
git add tea
git commit -m "Updating tea to the latest version."
git push
