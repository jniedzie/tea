#!/bin/bash

rm -fr build
rm -fr bin
mkdir build
cd build
cmake ..
make -j install 
cd ..
