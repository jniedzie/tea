#!/bin/bash

mkdir -p bin
mkdir -p build

rm -fr build/*
rm -fr bin/*

cd build

if ! command -v correction &> /dev/null; then
  cmake ..
else
  cmake $(correction config --cmake) ..
fi

make -j install 
cd ..

export PYTHONPATH="$PYTHONPATH:$(pwd)/bin/"
