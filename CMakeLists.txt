cmake_minimum_required(VERSION 3.8)
project(SiPMControl CXX)

## Compiler settings
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
#set(CMAKE_CXX_COMPILE_FEATURES cxx_variadic_templates)
set(CMAKE_CXX_EXTENSIONS OFF)
add_compile_options("-g")
add_compile_options("-O3")
add_compile_options("-Wall")
add_compile_options("-Wno-undef")

# General output settings
set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/cmod )
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/bin )

## Linux apple differences
if(UNIX AND NOT APPLE)
  set(BOOST_PYTHON_COMPONENTS "python39")
  set(PICO_FIND_PATH "/opt/picoscope/")
else()
  set(BOOST_PYTHON_COMPONENTS "python37")
  set(PICO_FIND_PATH "/Applications/PicoScope\ 6.app/Contents/Resources/")
endif()

set(PICO_INCLUDE_PATH "${PICO_FIND_PATH}/include/")
set(PICO_LIBRARY_PATH "${PICO_FIND_PATH}/lib/")

## Different architecture library differences.
set(PICO_HEADERS "libps5000/ps5000Api.h")

## Finding additional libraries
find_package(PythonLibs   3 REQUIRED)
find_package(PythonInterp 3 REQUIRED)
find_package(Boost          REQUIRED
             COMPONENTS ${BOOST_PYTHON_COMPONENTS}
             ${BOOST_PYTHON_NUMPY_COMPONENTS})
find_package(OpenCV         REQUIRED)
find_package(Threads        REQUIRED)

FILE(GLOB PICO_SRC pico/*.cc)
find_path( PICO_INCLUDES
  NAMES ${PICO_HEADERS}
  PATHS ${PICO_INCLUDE_PATH}  )
find_library(PICO_LIBS
  NAMES ps5000
  PATHS ${PICO_LIBRARY_PATH}  )
message(${Boost_INCLUDE_DIRS})
message(${PYTHON_INCLUDE_DIRS})

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

make_control_library( pico src/pico.cc )
target_include_directories(pico PRIVATE ${PICO_INCLUDES})
target_link_libraries(pico logger ${PICO_LIBS})

make_control_library( gcoder src/gcoder.cc )
target_link_libraries(gcoder logger )

make_control_library(gpio src/gpio.cc)
target_link_libraries(gpio Threads::Threads)

make_control_library( visual src/visual.cc)
target_link_libraries( visual logger ${OpenCV_LIBS} Threads::Threads)



## Add testing binary main files
add_executable( pico_test.exe bin/pico_test.cc )
target_include_directories(pico_test.exe PRIVATE ${PICO_INCLUDES} src/)
target_compile_definitions(pico_test.exe PUBLIC "STANDALONE")
target_link_libraries(pico_test.exe pico)

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

add_executable(visual_test.exe bin/visual_test.cc )
target_include_directories(visual_test.exe PRIVATE src/
    ${PYTHON_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
    "/usr/lib/python3.8/site-packages/numpy/core/include" )
target_link_libraries(visual_test.exe
                      visual
                      ${Boost_LIBRARIES}
                      ${PYTHON_LIBRARIES}
                      Threads::Threads)

## Making the GUI stuff
file(GLOB CSS_FILES ${PROJECT_SOURCE_DIR}/server/static/sass/*.scss)
add_custom_target(gen_server_css ALL
  COMMAND "sass" "style.scss:style.css"
  SOURCES ${CSS_FILES}
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/server/static
)
#add_custom_target(gen_server_css ALL DEPENDS server/static/style.css)
#add_dependencies(gen_server_css ${CSS_FILES})
