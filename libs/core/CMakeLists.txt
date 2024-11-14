cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project (core)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 14.5)

set(CMAKE_CXX_STANDARD 20)

cmake_policy(SET CMP0054 OLD)
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

# Detect the platform
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    set(PYTHON_LIBRARY_EXTENSION "dylib")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
    set(PYTHON_LIBRARY_EXTENSION "so")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Windows")
    set(PYTHON_LIBRARY_EXTENSION "dll")
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_SYSTEM_NAME}")
endif()

# find Python
# Check if CONDA_PREFIX is set
if(DEFINED ENV{CONDA_PREFIX})
    set(CONDA_PREFIX_PATH $ENV{CONDA_PREFIX})
    set(Python3_EXECUTABLE "${CONDA_PREFIX_PATH}/bin/python3")
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
    
    if(Python3_FOUND)
        # Set Python version variables manually if not set automatically
        if(NOT DEFINED Python3_VERSION_MAJOR)
            execute_process(COMMAND ${Python3_EXECUTABLE} -c "import sys; print(sys.version_info.major)"
                            OUTPUT_VARIABLE Python3_VERSION_MAJOR
                            OUTPUT_STRIP_TRAILING_WHITESPACE)
        endif()
        if(NOT DEFINED Python3_VERSION_MINOR)
            execute_process(COMMAND ${Python3_EXECUTABLE} -c "import sys; print(sys.version_info.minor)"
                            OUTPUT_VARIABLE Python3_VERSION_MINOR
                            OUTPUT_STRIP_TRAILING_WHITESPACE)
        endif()

        set(Python3_INCLUDE_DIR "${CONDA_PREFIX_PATH}/include/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}")
        set(Python3_LIBRARY "${CONDA_PREFIX_PATH}/lib/libpython${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}.${PYTHON_LIBRARY_EXTENSION}")    
        include_directories(${Python3_INCLUDE_DIR})
    else()
        message(FATAL_ERROR "Python3 not found in Conda environment")
    endif()
else()
    message(FATAL_ERROR "CONDA_PREFIX is not set. Please activate your Conda environment.")
endif()

# setup includes
include_directories("${PROJECT_SOURCE_DIR}/include")

# setup core library
file(GLOB SOURCES "src/*.cpp")
add_library(core SHARED ${SOURCES})

target_link_libraries(core PUBLIC ${Python3_LIBRARY} ${ROOT_LIBRARIES} correctionlib ZLIB::ZLIB Threads::Threads)
target_include_directories(core PUBLIC "${PROJECT_SOURCE_DIR}/include")

set_target_properties(core PROPERTIES INSTALL_RPATH "$ORIGIN/../tea/libs/core")
install(TARGETS core LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})

set_property(TARGET core PROPERTY CXX_STANDARD 20)
