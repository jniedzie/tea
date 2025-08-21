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
  cmake $(correction config --cmake) ..
fi

make -j install 
cd ..

export PYTHONPATH="$PYTHONPATH:$(pwd)/bin/"