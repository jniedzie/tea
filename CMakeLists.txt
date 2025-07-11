cmake_minimum_required(VERSION 3.14 FATAL_ERROR)
project(tea)

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
# set(CMAKE_INSTALL_RPATH "/cvmfs/sft.cern.ch/lcg/releases/vdt/0.4.3-992df/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/tbb/2019_U7-ba3eb/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/Davix/0.7.3-d94fa/x86_64-centos7-gcc8-opt/lib64/:/cvmfs/sft.cern.ch/lcg/releases/png/1.6.37-9c2fe/x86_64-centos7-gcc8-opt/lib/:/cvmfs/sft.cern.ch/lcg/releases/GSL/2.5-32fc5/x86_64-centos7-gcc8-opt/lib/")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

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

# Check if CONDA_PREFIX is set
if(NOT DEFINED ENV{CONDA_PREFIX})
    message(WARNING "CONDA_PREFIX is not set. Attempting to activate the base Conda environment.")

    # Attempt to activate Conda base environment
    execute_process(COMMAND bash -l -c "conda activate base && echo \$CONDA_PREFIX"
                    OUTPUT_VARIABLE CONDA_PREFIX_PATH
                    OUTPUT_STRIP_TRAILING_WHITESPACE
                    RESULT_VARIABLE CONDA_ACTIVATE_RESULT)

    if(NOT CONDA_ACTIVATE_RESULT EQUAL 0 OR "${CONDA_PREFIX_PATH}" STREQUAL "")
        message(FATAL_ERROR "Failed to activate Conda base environment. Please activate Conda manually.")
    endif()

    # Set the environment variable so subsequent commands can use it
    set(ENV{CONDA_PREFIX} ${CONDA_PREFIX_PATH})
endif()

set(CONDA_PREFIX_PATH $ENV{CONDA_PREFIX})
set(Python3_EXECUTABLE "${CONDA_PREFIX_PATH}/bin/python3")

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

    # Set the Python include directory and library
    message(STATUS "Deduced python version: ${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}")
    set(Python3_INCLUDE_DIR "${CONDA_PREFIX_PATH}/include/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}")
    set(Python3_LIBRARY "${CONDA_PREFIX_PATH}/lib/libpython${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}.${PYTHON_LIBRARY_EXTENSION}")
    message(STATUS "Python3 library: ${Python3_LIBRARY}")
    include_directories(${Python3_INCLUDE_DIR})
else()
    message(FATAL_ERROR "Python3 not found in Conda environment")
endif()

# add tea libraries and headers
set(LIBRARIES_DIR libs)
set(LIBRARIES core extensions histogramming)

foreach(LIBRARY ${LIBRARIES})
    add_subdirectory("${LIBRARIES_DIR}/${LIBRARY}")
    include_directories("${LIBRARIES_DIR}/${LIBRARY}/include")
endforeach(LIBRARY)

# add tea python libraries
add_subdirectory(pylibs)

# add tea apps
file(GLOB_RECURSE APP_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/apps/*/*.cpp")

foreach(APP_SOURCE ${APP_SOURCES})
   get_filename_component(APP_NAME ${APP_SOURCE} NAME_WE)
   
   add_executable(${APP_NAME} ${APP_SOURCE})
   target_link_libraries(${APP_NAME} PUBLIC core extensions histogramming ${ROOT_LIBRARIES} ${Python3_LIBRARY})
   
   set_property(TARGET ${APP_NAME} PROPERTY CXX_STANDARD 20)
   install(TARGETS ${APP_NAME} DESTINATION .)
endforeach()