cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project (core)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)

cmake_policy(SET CMP0068 NEW)

# setting for macOS
set(CMAKE_MACOSX_RPATH 1)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
set(CMAKE_INSTALL_RPATH "@loader_path/../bin")

# setup install directory to "bin"
set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}/bin")

# setup ROOT-specific variables
list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})
find_package(ROOT REQUIRED COMPONENTS Minuit Eve Geom)
include(${ROOT_USE_FILE})
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) 
set(CMAKE_INSTALL_RPATH "/cvmfs/sft.cern.ch/lcg/releases/vdt/0.4.3-992df/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/tbb/2019_U7-ba3eb/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/Davix/0.7.3-d94fa/x86_64-centos7-gcc8-opt/lib64/:/cvmfs/sft.cern.ch/lcg/releases/png/1.6.37-9c2fe/x86_64-centos7-gcc8-opt/lib/:/cvmfs/sft.cern.ch/lcg/releases/GSL/2.5-32fc5/x86_64-centos7-gcc8-opt/lib/")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# setup correctionlib
find_package(ZLIB REQUIRED)
find_package(correctionlib REQUIRED)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads)

get_target_property(CORRECTIONLIB_INCLUDE_DIRS correctionlib INTERFACE_INCLUDE_DIRECTORIES)
message(STATUS "correctionlib includes: ${CORRECTIONLIB_INCLUDE_DIRS}")
set(CORRECTIONLIB_INCLUDE_DIRS ${CORRECTIONLIB_INCLUDE_DIRS} CACHE INTERNAL "Correctionlib include dirs")

# find Python
find_package(Python3 REQUIRED)
find_package(PythonLibs REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

# setup includes
include_directories("${PROJECT_SOURCE_DIR}/include")

# setup core library
file(GLOB SOURCES "src/*.cpp")
add_library(core SHARED ${SOURCES})

target_link_libraries(core PUBLIC ${PYTHON_LIBRARIES} ${ROOT_LIBRARIES} correctionlib ZLIB::ZLIB Threads::Threads)
target_include_directories(core PUBLIC "${PROJECT_SOURCE_DIR}/include")

set_target_properties(core PROPERTIES INSTALL_RPATH "$ORIGIN/../tea/libs/core")
install(TARGETS core LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})

set_property(TARGET core PROPERTY CXX_STANDARD 17)