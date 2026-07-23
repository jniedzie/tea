cmake_minimum_required(VERSION 3.10..4.0 FATAL_ERROR)
project(tea)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 14.5)

if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wno-cpp)
endif()

cmake_policy(SET CMP0068 NEW)

# setting for macOS
set(CMAKE_MACOSX_RPATH 1)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
set(CMAKE_INSTALL_RPATH "@loader_path/../bin")

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
# set(CMAKE_INSTALL_RPATH "/cvmfs/sft.cern.ch/lcg/releases/vdt/0.4.3-992df/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/tbb/2019_U7-ba3eb/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/Davix/0.7.3-d94fa/x86_64-centos7-gcc8-opt/lib64/:/cvmfs/sft.cern.ch/lcg/releases/png/1.6.37-9c2fe/x86_64-centos7-gcc8-opt/lib/:/cvmfs/sft.cern.ch/lcg/releases/GSL/2.5-32fc5/x86_64-centos7-gcc8-opt/lib/")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

if(DEFINED ENV{CONDA_PREFIX} AND EXISTS "$ENV{CONDA_PREFIX}/bin/python3")
    set(Python3_EXECUTABLE "$ENV{CONDA_PREFIX}/bin/python3" CACHE FILEPATH "Python interpreter")
endif()

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
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
message(STATUS "Using Python3 executable: ${Python3_EXECUTABLE}")
message(STATUS "Using Python3 version: ${Python3_VERSION}")
message(STATUS "Using Python3 include dirs: ${Python3_INCLUDE_DIRS}")

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
   target_include_directories(${APP_NAME} PRIVATE ${Python3_INCLUDE_DIRS})
   target_link_libraries(${APP_NAME} PUBLIC core extensions histogramming ${ROOT_LIBRARIES} Python3::Python)
   
   set_property(TARGET ${APP_NAME} PROPERTY CXX_STANDARD ${CMAKE_CXX_STANDARD})
   install(TARGETS ${APP_NAME} DESTINATION .)
endforeach()
