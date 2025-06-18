cmake_minimum_required(VERSION 3.14 FATAL_ERROR)
project(user_analysis)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
SET(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)

# setup install directory to "bin"
set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}/bin")

# setup ROOT-specific variables
list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})
find_package(ROOT REQUIRED COMPONENTS Minuit Eve Geom)
include(${ROOT_USE_FILE})
SET(CMAKE_SKIP_BUILD_RPATH FALSE)
SET(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) 
SET(CMAKE_INSTALL_RPATH "/cvmfs/sft.cern.ch/lcg/releases/vdt/0.4.3-992df/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/tbb/2019_U7-ba3eb/x86_64-centos7-gcc8-opt/lib:/cvmfs/sft.cern.ch/lcg/releases/Davix/0.7.3-d94fa/x86_64-centos7-gcc8-opt/lib64/:/cvmfs/sft.cern.ch/lcg/releases/png/1.6.37-9c2fe/x86_64-centos7-gcc8-opt/lib/:/cvmfs/sft.cern.ch/lcg/releases/GSL/2.5-32fc5/x86_64-centos7-gcc8-opt/lib/")
SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# # find Python
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

    # Set the Python include directory and library
    message(STATUS "Deduced python version: ${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}")
    set(Python3_INCLUDE_DIR "${CONDA_PREFIX_PATH}/include/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}")
    set(Python3_LIBRARY "${CONDA_PREFIX_PATH}/lib/libpython${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}.${PYTHON_LIBRARY_EXTENSION}")

    message(STATUS "Python3 library: ${Python3_LIBRARY}")
    include_directories(${Python3_INCLUDE_DIR})
else()
    message(FATAL_ERROR "Python3 not found in Conda environment")
endif()

# setup tea as a subproject
add_subdirectory(tea)

message(STATUS "correctionlib includes at high_level: ${CORRECTIONLIB_INCLUDE_DIRS}")

# include all tea headers from tea/libs/*/include
file(GLOB LIBS_SUBDIRS "tea/libs/*")
foreach(SUBDIR ${LIBS_SUBDIRS})
    if(IS_DIRECTORY ${SUBDIR} AND EXISTS "${SUBDIR}/include")
        include_directories(${SUBDIR}/include)
    endif()
endforeach()

# add user-defined headers
file(GLOB LIBS_SUBDIRS "libs/*")
foreach(SUBDIR ${LIBS_SUBDIRS})
    if(IS_DIRECTORY ${SUBDIR} AND EXISTS "${SUBDIR}/include")
        include_directories(${SUBDIR}/include)
    endif()
endforeach()

include_directories(${CORRECTIONLIB_INCLUDE_DIRS})

# add user-defined libraries
file(GLOB_RECURSE USER_LIBS_SRC "${CMAKE_CURRENT_SOURCE_DIR}/libs/*/*.cpp") # Assuming the source files are in .cpp format
message(STATUS "Found user libs: ${USER_LIBS_SRC}")
if(USER_LIBS_SRC)
    add_library(user_libs ${USER_LIBS_SRC})
endif()

# add user-defined apps
file(GLOB_RECURSE USER_APPS_SRC "apps/*.cpp")
foreach(APP_SRC ${USER_APPS_SRC})
    get_filename_component(APP_NAME ${APP_SRC} NAME_WE) # Get the name without extension
    
    add_executable(${APP_NAME} ${APP_SRC})
    if(USER_LIBS_SRC)
        message(STATUS "Linking with user, tea, ROOT, and Python libs")
        target_link_libraries(${APP_NAME} PUBLIC user_libs core extensions histogramming ${ROOT_LIBRARIES} ${PYTHON_LIBRARIES})
    else()
        message(STATUS "Linking with tea, ROOT, and Python libs")
        target_link_libraries(${APP_NAME} PUBLIC core extensions histogramming ${ROOT_LIBRARIES} ${PYTHON_LIBRARIES})
    endif()

    set_property(TARGET ${APP_NAME} PROPERTY CXX_STANDARD 17)
    set_target_properties(${APP_NAME} PROPERTIES INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}")
    install(TARGETS ${APP_NAME} DESTINATION .)
endforeach()

# make links to python configs
file(GLOB_RECURSE PYTHON_CONFIGS "configs/*" "utils/*")
set(PYTHON_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}")

foreach(PYTHON_FILE ${PYTHON_CONFIGS})
    get_filename_component(PYTHON_FILENAME ${PYTHON_FILE} NAME)
    install(CODE "execute_process(COMMAND \${CMAKE_COMMAND} -E create_symlink \"${PYTHON_FILE}\" \"${PYTHON_INSTALL_DIR}/${PYTHON_FILENAME}\")")
endforeach()
