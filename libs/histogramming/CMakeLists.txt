cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project (histogramming)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 14.5)

if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

cmake_policy(SET CMP0068 NEW)

# setting for macOS
set(CMAKE_MACOSX_RPATH 1)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
set(CMAKE_INSTALL_RPATH "@loader_path/../bin")

# setup ROOT-specific variables
find_program(ROOT_CONFIG_EXECUTABLE root-config)
if(ROOT_CONFIG_EXECUTABLE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --prefix OUTPUT_VARIABLE ROOT_CONFIG_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --incdir OUTPUT_VARIABLE ROOT_CONFIG_INCDIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --libdir OUTPUT_VARIABLE ROOT_CONFIG_LIBDIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --cxxstandard OUTPUT_VARIABLE ROOT_CONFIG_CXXSTANDARD OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)

    if(ROOT_CONFIG_CXXSTANDARD MATCHES "^[0-9]+$")
        set(CMAKE_CXX_STANDARD "${ROOT_CONFIG_CXXSTANDARD}")
    endif()

    set(CMAKE_PREFIX_PATH "${ROOT_CONFIG_PREFIX};${ROOT_CONFIG_PREFIX}/cmake;${ROOT_CONFIG_LIBDIR}/cmake/ROOT;${CMAKE_PREFIX_PATH}")
    set(CMAKE_INCLUDE_PATH "${ROOT_CONFIG_INCDIR};${CMAKE_INCLUDE_PATH}")
    set(CMAKE_LIBRARY_PATH "${ROOT_CONFIG_LIBDIR};${CMAKE_LIBRARY_PATH}")

    if(EXISTS "${ROOT_CONFIG_PREFIX}/cmake/ROOTConfig.cmake")
        set(ROOT_DIR "${ROOT_CONFIG_PREFIX}/cmake" CACHE PATH "ROOT CMake package directory" FORCE)
    elseif(EXISTS "${ROOT_CONFIG_LIBDIR}/cmake/ROOT/ROOTConfig.cmake")
        set(ROOT_DIR "${ROOT_CONFIG_LIBDIR}/cmake/ROOT" CACHE PATH "ROOT CMake package directory" FORCE)
    endif()
endif()
if(DEFINED ENV{ROOTSYS} AND NOT "$ENV{ROOTSYS}" STREQUAL "")
    set(CMAKE_PREFIX_PATH "$ENV{ROOTSYS};${CMAKE_PREFIX_PATH}")
endif()
set(TEA_ROOT_COMPONENTS Core RIO Tree Hist Graf Gpad Matrix Physics MathCore)
find_package(ROOT REQUIRED COMPONENTS ${TEA_ROOT_COMPONENTS})
include(${ROOT_USE_FILE})
include_directories(${ROOT_INCLUDE_DIRS} ${ROOT_CONFIG_INCDIR})
SET(CMAKE_SKIP_BUILD_RPATH FALSE)
SET(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) 
SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

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
message(STATUS "histogramming using Python3 include dirs: ${Python3_INCLUDE_DIRS}")

# setup histogramming library
file(GLOB SOURCES "src/*.cpp")
add_library(histogramming SHARED ${SOURCES})

add_dependencies(histogramming extensions)
target_include_directories(histogramming PUBLIC ${Python3_INCLUDE_DIRS})
target_link_libraries(histogramming PUBLIC Python3::Python core extensions)
target_include_directories(histogramming PUBLIC "${PROJECT_SOURCE_DIR}/include")

set_target_properties(histogramming PROPERTIES INSTALL_RPATH "$ORIGIN/../tea/libs/histogramming")
install(TARGETS histogramming LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})

set_property(TARGET histogramming PROPERTY CXX_STANDARD ${CMAKE_CXX_STANDARD})
