cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project(tea)

# setup variables for macOS builds
set(CMAKE_OSX_ARCHITECTURES "arm64")
set(CMAKE_OSX_DEPLOYMENT_TARGET 13.2)

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

# find Python
find_package(Python3 REQUIRED)
find_package(PythonLibs REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

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
   target_link_libraries(${APP_NAME} PUBLIC core extensions histogramming ${ROOT_LIBRARIES} ${PYTHON_LIBRARIES})
   
   set_property(TARGET ${APP_NAME} PROPERTY CXX_STANDARD 17)
   install(TARGETS ${APP_NAME} DESTINATION .)
endforeach()
