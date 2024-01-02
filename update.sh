#!/bin/bash

# update tea
cd tea
git checkout main
git pull origin main

cd ..
git add tea
git commit -m "Updating tea to the latest version."
git push
