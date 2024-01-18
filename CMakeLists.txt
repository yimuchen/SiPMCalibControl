cmake_minimum_required(VERSION 3.8)
project(rocv2 CXX)

## Compiler settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_compile_options("-g")
add_compile_options("-O3")
add_compile_options("-Wall")
add_compile_options("-Wno-undef")

# General output settings
set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/src/gantry_control/tbc)

## Finding common required binary
find_package(PythonLibs    3 REQUIRED)
find_package(PythonInterp  3 REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(Boost COMPONENTS serialization)

pybind11_add_module(_rocv2 SHARED ${CMAKE_HOME_DIRECTORY}/src/gantry_control/tbc/_rocv2.cc)
target_include_directories(_rocv2
                           PRIVATE
                           ${PYTHON_INCLUDE_DIRS}
                           ${CMAKE_HOME_DIRECTORY}/src/gantry_control/tbc/)
target_link_libraries(_rocv2 PRIVATE ${PYTHON_LIBRARIES} ${Boost_LIBRARIES})

