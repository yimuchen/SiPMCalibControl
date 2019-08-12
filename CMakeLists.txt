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
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/cmod )
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/bin )

## Finding additional libraries
find_package(PythonLibs   3 REQUIRED)
find_package(PythonInterp 3 REQUIRED)
find_package(Boost          REQUIRED COMPONENTS python3)
find_package(OpenCV         REQUIRED)

FILE(GLOB PICO_SRC pico/*.cc)
find_path( PICO_INCLUDES
  NAMES libps5000/ps5000Api.h
  PATHS /opt/picoscope/include/
  )
find_library(PICO_LIBS
  NAMES ps5000
  PATHS /opt/picoscope/lib/
  )

# Only attempt to link wiring pi in a ARM machine
if(${CMAKE_SYSTEM_PROCESSOR} MATCHES "arm")
  find_library( WIRINGPI_LIBS
   NAMES wiringPi wiringPiDev
   PATHS /usr/lib/)
endif()

## Libraries are supposed to be python modules
function(make_control_library libname source )
  add_library(${libname} SHARED ${source})
  set_target_properties( ${libname} PROPERTIES PREFIX "" )
  target_include_directories(${libname} PRIVATE ${PYTHON_INCLUDE_DIRS} )
  target_link_libraries(${libname}
    ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} )
endfunction()

make_control_library( logger src/logger.cc )

make_control_library( pico src/pico.cc )
target_include_directories(pico PRIVATE ${PICO_INCLUDES})
target_link_libraries(pico logger ${PICO_LIBS})

make_control_library( gcoder src/gcoder.cc )
target_link_libraries(gcoder logger )

make_control_library( visual src/visual.cc )
target_link_libraries( visual logger ${OpenCV_LIBS} )

make_control_library(trigger src/trigger.cc )
# For a non-ARM maching, don't attempt to link WIRING_PI
if(${CMAKE_SYSTEM_PROCESSOR} MATCHES "arm")
  target_link_libraries(trigger logger ${WIRINGPI_LIBS} )
else()
  message( WARNING "Trigger is a dummy call that only sleeps the threads")
  add_compile_definitions(NO_WIRING)
endif()



## Add testing binary main files
add_executable( mytest.exe bin/mytest.cc )
target_include_directories(mytest.exe PRIVATE ${PICO_INCLUDES} src/)
target_link_libraries(mytest.exe pico)

add_executable( triggerpulse.exe bin/triggerpulse.cc )

# For a non-ARM maching, don't attempt to link WIRING_PI
if(${CMAKE_SYSTEM_PROCESSOR} MATCHES "arm")
  target_link_libraries( triggerpulse.exe ${WIRINGPI_LIBS} )
endif()
