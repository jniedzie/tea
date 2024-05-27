cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project (extensions)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)

cmake_policy(SET CMP0068 NEW)

# setting for macOS
set(CMAKE_MACOSX_RPATH 1)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
set(CMAKE_INSTALL_RPATH "@loader_path/../bin")

# setup ROOT-specific variables
list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})
find_package(ROOT REQUIRED COMPONENTS Minuit Eve Geom)
include(${ROOT_USE_FILE})
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) 
set(CMAKE_INSTALL_RPATH "/cvmfs/sft.cern.ch/lcg/releases/vdt/0.4.3-992df/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/tbb/2019_U7-ba3eb/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/Davix/0.7.3-d94fa/x86_64-centos7-gcc8-opt/lib64/:/cvmfs/sft.cern.ch/lcg/releases/png/1.6.37-9c2fe/x86_64-centos7-gcc8-opt/lib/:/cvmfs/sft.cern.ch/lcg/releases/GSL/2.5-32fc5/x86_64-centos7-gcc8-opt/lib/")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# find Python
find_package(Python3 REQUIRED)
find_package(PythonLibs REQUIRED)
include_directories("${PROJECT_SOURCE_DIR}/include" ${PYTHON_INCLUDE_DIRS})

# setup extensions library
file(GLOB SOURCES "src/*.cpp")
add_library(extensions SHARED ${SOURCES})

add_dependencies(extensions core)
target_link_libraries(extensions PUBLIC ${PYTHON_LIBRARIES} core)
target_include_directories(extensions PUBLIC "${PROJECT_SOURCE_DIR}/include")

set_target_properties(extensions PROPERTIES INSTALL_RPATH "$ORIGIN/../tea/libs/extensions")
install(TARGETS extensions LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})

set_property(TARGET extensions PROPERTY CXX_STANDARD 17)
