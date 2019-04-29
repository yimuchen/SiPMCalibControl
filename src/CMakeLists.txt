## All other stuff in the boost directory
find_package(PythonLibs   3 REQUIRED)
find_package(PythonInterp 3 REQUIRED)
find_package(Boost          REQUIRED COMPONENTS python3)
find_package(OpenCV         REQUIRED)

INCLUDE_DIRECTORIES(gcoder/ session/ trigger/ common/)

## Common stuff
FILE(GLOB COMMON_SRC common/*.cc)
add_library(Common SHARED ${COMMON_SRC})

## g-code streaming part
FILE(GLOB GCODER_SRC gcoder/*.cc)
add_library(GCoder SHARED ${GCODER_SRC})
add_dependencies(GCoder Common)
target_link_libraries(GCoder Common )

## visual processing part
FILE(GLOB VISUAL_SRC visual/*.cc)
add_library(Visual SHARED ${VISUAL_SRC})
add_dependencies(Visual Common)
target_link_libraries(Visual ${OpenCV_LIBS} Common)

## GPIO part
FILE(GLOB TRIGGER_SRC trigger/*.cc )
add_library(Trigger SHARED ${TRIGGER_SRC})

## PICOSCOPE part
FILE(GLOB PICO_SRC pico/*.cc)
find_path( PICO_INCLUDES
  NAMES libps5000-1.5/ps5000Api.h
  PATHS /opt/picoscope/include/
  )
find_library(PICO_LIBS
  NAMES ps5000
  PATHS /opt/picoscope/lib/
  )
add_library(Pico SHARED ${PICO_SRC})
target_include_directories(Pico PRIVATE ${PICO_INCLUDES})
target_link_libraries(Pico ${PICO_LIBS} Common)

add_executable( mytest.exe testbin/mytest.cc )
target_include_directories(mytest.exe PRIVATE pico ${PICO_INCLUDES})
target_link_libraries(mytest.exe Pico)
#
# add_executable( picotest.exe pico/picotest.c )
# target_include_directories(picotest.exe PRIVATE ${PICO_INCLUDES})
# target_link_libraries(picotest.exe ${PICO_LIBS} Common)






## Boost-python libraries
function(make_boost_python libname depname )
  add_library(${libname} SHARED boost/${libname}.cc )
  set_target_properties(${libname} PROPERTIES PREFIX "../cmod/")
  target_include_directories(${libname} PRIVATE ${libname}/)
  target_include_directories(${libname} PRIVATE ${PYTHON_INCLUDE_DIRS})
  target_link_libraries(${libname}
    ${Boost_LIBRARIES} ${PYTHON_LIBRARIES}
    ${depname})
endfunction()

make_boost_python( gcoder  GCoder )
make_boost_python( logger  Common )
make_boost_python( visual  Visual )
make_boost_python( trigger Trigger )
make_boost_python( pico    Pico )
