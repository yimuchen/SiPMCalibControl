cmake_minimum_required(VERSION 3.8)
project(SiPMControl CXX)

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
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/cmod )
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/bin )

## Finding common required binary
find_package(PythonLibs    3 REQUIRED)
find_package(PythonInterp  3 REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(OpenCV          REQUIRED)
find_package(Threads         REQUIRED)
find_package(fmt             REQUIRED)
find_package(Boost COMPONENTS serialization)


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
    target_link_libraries(${target_name} PRIVATE drs_base)
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

# The python logging pass thorugh as a separate library
add_library(c_logger SHARED src/logger.cc)
target_include_directories(c_logger PRIVATE ${PYTHON_INCLUDE_DIRS})
target_link_libraries(c_logger PRIVATE  ${PYTHON_LIBRARIES})

## Libraries are supposed to be python modules
function(make_control_library libname source)
  add_library(c_${libname} SHARED ${source})
  get_filename_component(basename ${source} NAME)
  pybind11_add_module(${libname} SHARED cmod/py_${basename})
  target_include_directories(${libname} PRIVATE "src/" )
  target_link_libraries(${libname} PRIVATE c_${libname})
endfunction()

# Making the various interface classes
if( DRS_DEFINES )
  make_control_library(drs src/drs.cc)
  add_drs_requirements(drs)
  add_drs_requirements(c_drs)
  target_link_libraries(c_drs PRIVATE c_logger fmt::fmt)
endif()

if( PICOSCOPE_LIB )
  make_control_library( pico src/pico.cc )
  target_include_directories(c_pico PRIVATE ${PICOSCOPE_INCDIR})
  target_link_directories(c_pico PRIVATE ${PICOSCOPE_LIBDIR})
  target_link_libraries(c_pico PRIVATE c_logger ${PICOSCOPE_LIB} fmt::fmt)
endif()

make_control_library(gcoder src/gcoder.cc )
target_link_libraries(gcoder PRIVATE c_logger fmt::fmt)

make_control_library(gpio src/gpio.cc)
target_link_libraries(gpio PRIVATE c_logger Threads::Threads fmt::fmt)

make_control_library( visual src/visual.cc)
target_link_libraries( c_visual PRIVATE  c_logger
                                         ${OpenCV_LIBS}
                                         Threads::Threads
                                         pybind11::pybind11
                                         pybind11::python_link_helper
                                         fmt::fmt)
#message( "TESTING" ${PYTHON#_INCLUDE_DIRS} )
target_include_directories(c_visual PRIVATE ${OpenCV_INCLUDE_DIRS}
                                            ${PYTHON_INCLUDE_DIRS} )
target_include_directories(visual PRIVATE ${OpenCV_INCLUDE_DIRS} )

if( EXISTS "external/hexactrl-sw/" )
  message("External package for picoscope found! "
          "Making the picoscope readout interface")
  pybind11_add_module(_rocv2 SHARED cmod/_rocv2.cc)
  target_include_directories(_rocv2
                             PRIVATE
                             ${PYTHON_INCLUDE_DIRS}
                             ${CMAKE_HOME_DIRECTORY}/external/hexactrl-sw)
  target_link_libraries(_rocv2 PRIVATE  ${PYTHON_LIBRARIES} ${Boost_LIBRARIES})
endif()

## Add testing binary files
# if( PICOSCOPE_LIB )
#   add_executable( pico_test.exe bin/pico_test.cc )
#   target_include_directories(pico_test.exe PRIVATE ${PICOSCOPE_INCDIR} src/)
#   target_compile_definitions(pico_test.exe PUBLIC "STANDALONE")
#   target_link_directories(pico_test.exe PRIVATE ${PICOSCOPE_LIBDIR})
#   target_link_libraries(pico_test.exe pico)
# endif()

## Testing Binay systems
# if( DRS_DEFINES )
#   add_executable(drs_test.exe bin/drs_test.cc)
#   add_drs_requirements(drs_test.exe)
#   target_include_directories(drs_test.exe PRIVATE "src/")
#   target_compile_definitions(drs_test.exe PRIVATE STANDALONE)
#   target_link_libraries(drs_test.exe logger drs_base)
# endif()


# add_executable(gpio_test.exe bin/gpio_test.cc )
# target_include_directories(gpio_test.exe PRIVATE src/)
# target_compile_definitions(gpio_test.exe PUBLIC "STANDALONE" )
# target_link_libraries(gpio_test.exe Threads::Threads)

# add_executable(logger_test.exe bin/logger_test.cc )
# target_include_directories(logger_test.exe PRIVATE src/)
# target_compile_definitions(logger_test.exe PUBLIC "STANDALONE" )
# target_link_libraries(logger_test.exe logger)

add_executable(visual_test.exe bin/visual_test.cc )
target_include_directories(visual_test.exe PRIVATE src/
                                                   ${OpenCV_INCLUDE_DIRS}
                                                   ${PYTHON_INCLUDE_DIRS})
target_link_libraries(visual_test.exe PRIVATE c_visual
                                              Threads::Threads
                                              ${OpenCV_LIBS}
                                              ${PYTHON_LIBRARIES})
message("PYBIND11 libraries " ${pybind11_LIBRARIES})

# add_executable(gcoder_test.exe bin/gcoder_test.cc )
# target_include_directories(gcoder_test.exe PRIVATE src/)
# target_compile_definitions(gcoder_test.exe PUBLIC "STANDALONE" )
# target_link_libraries(gcoder_test.exe gcoder Threads::Threads)

## Making the GUI stuff
file(GLOB CSS_FILES ${PROJECT_SOURCE_DIR}/server/sass/*.scss)
add_custom_target(gen_server_css ALL
  COMMAND "sass" "style.scss:style.css"
  SOURCES ${CSS_FILES}
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/server)
#add_custom_target(gen_server_css ALL DEPENDS server/static/style.css)
#add_dependencies(gen_server_css ${CSS_FILES})
