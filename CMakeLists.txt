cmake_minimum_required(VERSION 3.8)
project(SiPMControl CXX)

## Compiler settings
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_compile_options("-g")
add_compile_options("-O3")
add_compile_options("-Wall")
add_compile_options("-Wno-undef")

# General output settings
set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/cmod )
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/bin )

## Finding common required binary
find_package(PythonLibs   3 REQUIRED)
find_package(PythonInterp 3 REQUIRED)
#find_package(pybind11 CONFIG REQUIRED)
find_package(Boost          REQUIRED
             COMPONENTS ${BOOST_PYTHON_COMPONENTS}
             ${BOOST_PYTHON_NUMPY_COMPONENTS})
find_package(OpenCV         REQUIRED)
find_package(Threads        REQUIRED)

## The DRS4 library, this assumes that the stuff have been added to the
if( EXISTS "external/drs" )
  message("External package DRS found! Making the DRS readout interface")

  # Must use the wxwidgets... for some reason
  find_package(wxWidgets COMPONENTS core base)
  if(NOT wxWidgets_FOUND)
    message(FATAL_ERROR "DRS must require wx widgets to be installed")
  endif()

  include(${wxWidgets_USE_FILE})

  # Selecting the minimum required files for running the interface defined in the
  # DRS.hpp interface.
  set(DRS_DEFINES OS_LINUX HAVE_LIBUSB HAVE_LIBUSB10 USE_DRS_MUTEX)
  set(DRS_SRC "external/drs/src/DRS.cpp"
              "external/drs/src/averager.cpp"
              "external/drs/src/mxml.c"
              "external/drs/src/strlcpy.c"
              "external/drs/src/musbstd.c")
  # Since there is are stray c files, force to be compiled as C++
  set_source_files_properties(${DRS_SRC} PROPERTIES LANGUAGE CXX )
  add_library(drs_base SHARED ${DRS_SRC})
  target_include_directories(drs_base PRIVATE
                             "external/drs/include/")
  target_compile_definitions(drs_base PRIVATE ${DRS_DEFINES})
  target_link_libraries(drs_base usb ${wxWidgets_LIBRARIES})

  # Creating a new function to help with making DRS related targets
  function( add_drs_requirements target_name )
    target_include_directories(${target_name} PRIVATE
                               "external/drs/include")
    target_compile_definitions(${target_name} PRIVATE
                               ${DRS_DEFINES})
    target_link_libraries(${target_name} drs_base)
  endfunction()
endif()

# The Picoscope library, this assumes that the interface has been added to the
# external directory
if( EXISTS "external/picoscope" )
  message("External package for picoscope found! "
          "Making the picoscope readout interface")
  set(PICOSCOPE_INCDIR  "external/picoscope/include/")
  set(PICOSCOPE_LIBDIR  "external/picoscope/lib/")
  set(PICOSCOPE_LIB     "ps5000")
endif()


## Libraries are supposed to be python modules
function(make_control_library libname source )
  add_library(${libname} SHARED ${source})
  set_target_properties( ${libname} PROPERTIES PREFIX "" )
  target_include_directories(${libname} PRIVATE
    ${PYTHON_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS} )
  target_link_libraries(${libname}
    ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} "boost_numpy3")
endfunction()

make_control_library( logger src/logger.cc )

## Making the various interface classes
if( DRS_DEFINES )
  make_control_library(drs src/drs.cc)
  add_drs_requirements(drs)
  target_link_libraries(drs logger)
endif()

if( PICOSCOPE_LIB )
  make_control_library( pico src/pico.cc )
  target_include_directories(pico PRIVATE ${PICOSCOPE_INCDIR})
  target_link_directories(pico PRIVATE ${PICOSCOPE_LIBDIR})
  target_link_libraries(pico logger ${PICOSCOPE_LIB})
endif()

make_control_library( gcoder src/gcoder.cc )
target_link_libraries(gcoder logger )

make_control_library(gpio src/gpio.cc)
target_link_libraries(gpio Threads::Threads)

make_control_library( visual src/visual.cc)
target_link_libraries( visual logger ${OpenCV_LIBS} Threads::Threads)



## Add testing binary files
if( PICOSCOPE_LIB )
  add_executable( pico_test.exe bin/pico_test.cc )
  target_include_directories(pico_test.exe PRIVATE ${PICOSCOPE_INCDIR} src/)
  target_compile_definitions(pico_test.exe PUBLIC "STANDALONE")
  target_link_directories(pico_test.exe PRIVATE ${PICOSCOPE_LIBDIR})
  target_link_libraries(pico_test.exe pico)
endif()

## Testing Binay systems
if( DRS_DEFINES )
  add_executable(drs_test.exe bin/drs_test.cc)
  add_drs_requirements(drs_test.exe)
  target_include_directories(drs_test.exe PRIVATE "src/")
  target_compile_definitions(drs_test.exe PRIVATE STANDALONE)
  target_link_libraries(drs_test.exe logger drs_base)
endif()


add_executable(gpio_test.exe bin/gpio_test.cc )
target_include_directories(gpio_test.exe PRIVATE src/)
target_compile_definitions(gpio_test.exe PUBLIC "STANDALONE" )
target_link_libraries(gpio_test.exe Threads::Threads)

add_executable(logger_test.exe bin/logger_test.cc )
target_include_directories(logger_test.exe PRIVATE src/)
target_compile_definitions(logger_test.exe PUBLIC "STANDALONE" )
target_link_libraries(logger_test.exe logger)


add_executable(gcoder_test.exe bin/gcoder_test.cc )
target_include_directories(gcoder_test.exe PRIVATE src/)
target_compile_definitions(gcoder_test.exe PUBLIC "STANDALONE" )
target_link_libraries(gcoder_test.exe gcoder Threads::Threads)

## Making the GUI stuff
file(GLOB CSS_FILES ${PROJECT_SOURCE_DIR}/server/static/sass/*.scss)
add_custom_target(gen_server_css ALL
  COMMAND "sass" "style.scss:style.css"
  SOURCES ${CSS_FILES}
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/server/static)
#add_custom_target(gen_server_css ALL DEPENDS server/static/style.css)
#add_dependencies(gen_server_css ${CSS_FILES})
