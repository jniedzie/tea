cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
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

# find Python
find_package(Python3 REQUIRED)
find_package(PythonLibs REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

# setup tea as a subproject
add_subdirectory(tea)

# include all tea headers from tea/libs/*/include
file(GLOB LIBS_SUBDIRS "tea/libs/*")
foreach(SUBDIR ${LIBS_SUBDIRS})
    if(IS_DIRECTORY ${SUBDIR} AND EXISTS "${SUBDIR}/include")
        include_directories(${SUBDIR}/include)
    endif()
endforeach()

# add tea libraries
file(GLOB_RECURSE TEA_LIBS_SRC "${CMAKE_CURRENT_SOURCE_DIR}/tea/libs/*/*.cpp") # Assuming the source files are in .cpp format
add_library(tea_libs ${TEA_LIBS_SRC})

# add user-defined headers
file(GLOB LIBS_SUBDIRS "libs/*")
foreach(SUBDIR ${LIBS_SUBDIRS})
    if(IS_DIRECTORY ${SUBDIR} AND EXISTS "${SUBDIR}/include")
        include_directories(${SUBDIR}/include)
    endif()
endforeach()

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
        target_link_libraries(${APP_NAME} user_libs tea_libs ${ROOT_LIBRARIES} ${PYTHON_LIBRARIES})
    else()
        message(STATUS "Linking with tea, ROOT, and Python libs")
        target_link_libraries(${APP_NAME} tea_libs ${ROOT_LIBRARIES} ${PYTHON_LIBRARIES})
    endif()

    set_property(TARGET ${APP_NAME} PROPERTY CXX_STANDARD 17)
    install(TARGETS ${APP_NAME} DESTINATION .)
endforeach()

# make links to python configs
file(GLOB_RECURSE PYTHON_CONFIGS "configs/*.py")

set(PYTHON_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}")

foreach(PYTHON_FILE ${PYTHON_CONFIGS})
    get_filename_component(PYTHON_FILENAME ${PYTHON_FILE} NAME)
    install(CODE "execute_process(COMMAND \${CMAKE_COMMAND} -E create_symlink \"${PYTHON_FILE}\" \"${PYTHON_INSTALL_DIR}/${PYTHON_FILENAME}\")")
endforeach()
