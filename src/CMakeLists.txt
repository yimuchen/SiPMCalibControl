## g-code streaming part
FILE(GLOB GCODE_SRC gcode/*.cc)
add_library(GCode SHARED ${GCODE_SRC})

FILE(GLOB TDAQ_SRC tdaq/*.cc)
add_library(TDaQ SHARED ${TDAQ_SRC})

## All other stuff in the boost directory
find_package(PythonLibs   3 REQUIRED)
find_package(PythonInterp 3 REQUIRED)
find_package(Boost          REQUIRED COMPONENTS python3)

INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})
LINK_LIBRARIES(${Boost_LIBRARIES} ${PYTHON_LIBRARIES})

add_library(gcodestream SHARED boost/gcodestream.cc )
set_target_properties(gcodestream PROPERTIES PREFIX "../python/")
target_include_directories(gcodestream PRIVATE gcode/)
target_link_libraries(gcodestream ${Boost_LIBRARIES} GCode)

add_library(tdaq SHARED boost/tdaq.cc )
set_target_properties(tdaq PROPERTIES PREFIX "../python/")
target_include_directories(tdaq PRIVATE tdaq/)
target_link_libraries(tdaq ${Boost_LIBRARIES} TDaQ)
