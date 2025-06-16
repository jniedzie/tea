#!/bin/bash

# docker build --platform=linux/arm64 -f Dockerfile.jekyll -t my-jekyll .
docker run --rm -p 4000:4000 my-jekyll
