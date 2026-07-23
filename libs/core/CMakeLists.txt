cmake_minimum_required(VERSION 3.14...4.0 FATAL_ERROR)
project (core)

if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)

cmake_policy(SET CMP0068 NEW)

# setup install directory to "bin"
set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}/bin")

# setup ROOT-specific variables
find_program(ROOT_CONFIG_EXECUTABLE root-config)
if(ROOT_CONFIG_EXECUTABLE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --prefix OUTPUT_VARIABLE ROOT_CONFIG_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --incdir OUTPUT_VARIABLE ROOT_CONFIG_INCDIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --libdir OUTPUT_VARIABLE ROOT_CONFIG_LIBDIR OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${ROOT_CONFIG_EXECUTABLE} --cxxstandard OUTPUT_VARIABLE ROOT_CONFIG_CXXSTANDARD OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)

    if(ROOT_CONFIG_CXXSTANDARD MATCHES "^[0-9]+$" AND ROOT_CONFIG_CXXSTANDARD GREATER CMAKE_CXX_STANDARD)
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
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) 
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

find_package(ZLIB REQUIRED)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads)

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

find_package(correctionlib QUIET)
if(NOT correctionlib_FOUND)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c
                "import pathlib, correctionlib; print(pathlib.Path(correctionlib.__file__).parent / 'cmake')"
        OUTPUT_VARIABLE correctionlib_CMAKE_PATH
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(correctionlib_CMAKE_PATH)
        find_package(correctionlib QUIET PATHS "${correctionlib_CMAKE_PATH}" NO_DEFAULT_PATH)
    endif()
endif()

# setup includes
include_directories("${PROJECT_SOURCE_DIR}/include")
target_include_directories(core PUBLIC ${Python3_INCLUDE_DIRS})

target_link_libraries(core PUBLIC Python3::Python ${ROOT_LIBRARIES} ZLIB::ZLIB Threads::Threads)

if(correctionlib_FOUND)
  message(STATUS "correctionlib target found. Linking with correctionlib::correctionlib.")
  target_link_libraries(core PUBLIC correctionlib)
  target_compile_definitions(core PUBLIC -DUSE_CORRECTIONLIB)
else()
  message(WARNING "correctionlib target not found. Building without correctionlib.")
endif()
target_include_directories(core PUBLIC "${PROJECT_SOURCE_DIR}/include")

set_target_properties(core PROPERTIES INSTALL_RPATH "${TEA_INSTALL_RPATH}")
install(TARGETS core LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})

set_property(TARGET core PROPERTY CXX_STANDARD ${CMAKE_CXX_STANDARD})
