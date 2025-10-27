#!/bin/bash

mkdir -p bin
mkdir -p build

if [[ "$1" == "--clean" ]]; then
  echo "Cleaning build and bin directories..."
  rm -fr build/*
  rm -fr bin/*
fi

cd build

if ! command -v correction &> /dev/null; then
  cmake ..
else
  cmake $(PYTHONNOUSERSITE=1 correction config --cmake) ..
fi

make -j install
cd ..

# make links to all python files, even if not rebuilding. Include directories (if exist, and recursively):
# configs, utils, tea/configs:

cd bin
find ../ -name "*.py" -type f -exec ln -sf {} . \;
cd ..


export PYTHONPATH="$PYTHONPATH:$(pwd)/bin/"