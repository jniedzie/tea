#!/bin/bash

mkdir -p bin
mkdir -p build

rm -fr build/*
rm -fr bin/*

cd build
cmake ..
make -j install 
cd ..

source tea/setup.sh
