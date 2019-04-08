cmake_minimum_required(VERSION 3.0)
project(SiPMControl)

## Compilter settings
set(CMAKE_CXX_COMPILE_FEATURES cxx_range_for )
set(CMAKE_CXX_COMPILE_FEATURES cxx_variadic_templates)
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_compile_options("-g")
add_compile_options("-O3")
add_compile_options("-Wall")
add_compile_options("-Wno-undef")

# General output settings
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/lib )

## Defining libraries
add_subdirectory(src)
