cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project (core)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 14.5)

set(CMAKE_CXX_STANDARD 17)

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

find_package(ZLIB REQUIRED)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads)
find_package(correctionlib QUIET)

# setup core library
file(GLOB SOURCES "src/*.cpp")
add_library(core SHARED ${SOURCES})


if(NOT TARGET Python3::Python)
    if(DEFINED ENV{CONDA_PREFIX} AND EXISTS "$ENV{CONDA_PREFIX}/bin/python3")
        set(Python3_EXECUTABLE "$ENV{CONDA_PREFIX}/bin/python3" CACHE FILEPATH "Python interpreter")
    endif()
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
endif()
if(NOT Python3_INCLUDE_DIRS OR NOT EXISTS "${Python3_INCLUDE_DIRS}/Python.h")
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_path('include') or '')"
        OUTPUT_VARIABLE Python3_INCLUDE_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()
if(NOT Python3_INCLUDE_DIRS OR NOT EXISTS "${Python3_INCLUDE_DIRS}/Python.h")
    message(FATAL_ERROR "Python3 headers not found for ${Python3_EXECUTABLE}. Expected Python.h under ${Python3_INCLUDE_DIRS}.")
endif()
message(STATUS "core using Python3 include dirs: ${Python3_INCLUDE_DIRS}")

# setup includes
include_directories("${PROJECT_SOURCE_DIR}/include")
target_include_directories(core PUBLIC ${Python3_INCLUDE_DIRS})

target_link_libraries(core PUBLIC Python3::Python ${ROOT_LIBRARIES} ZLIB::ZLIB Threads::Threads)

if(correctionlib_FOUND)
  message(STATUS "correctionlib target found. Linking with correctionlib::correctionlib.")
  target_link_libraries(core PRIVATE correctionlib)
  target_compile_definitions(core PRIVATE -DUSE_CORRECTIONLIB)
else()
  message(WARNING "correctionlib target not found. Building without correctionlib.")
endif()
target_include_directories(core PUBLIC "${PROJECT_SOURCE_DIR}/include")

set_target_properties(core PROPERTIES INSTALL_RPATH "$ORIGIN/../tea/libs/core")
install(TARGETS core LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})

set_property(TARGET core PROPERTY CXX_STANDARD 17)
