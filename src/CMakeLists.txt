INCLUDE_DIRECTORIES(gcoder/ session/ board/ trigger/)

## Common stuff
FILE(GLOB COMMON_SRC common/*.cc)
add_library(Common SHARED ${COMMON_SRC})

# Board information storage type
FILE(GLOB BOARD_SRC board/*.cc)
add_library(Board SHARED ${BOARD_SRC})

## g-code streaming part
FILE(GLOB GCODER_SRC gcoder/*.cc)
add_library(GCoder SHARED ${GCODER_SRC})
add_dependencies(GCoder Common)
target_include_directories(GCoder PRIVATE common/)
target_link_libraries(GCoder Common)

## visual processing part
FILE(GLOB VISUAL_SRC visual/*.cc)
add_library(Visual SHARED ${VISUAL_SRC})
find_package(OpenCV REQUIRED )
add_dependencies(Visual Common)
target_include_directories(Visual PRIVATE common/)
target_link_libraries(Visual ${OpenCV_LIBS} Common)

## GPIO part
FILE(GLOB TRIGGER_SRC trigger/*.cc )
add_library(Trigger SHARED ${TRIGGER_SRC})


## All other stuff in the boost directory
find_package(PythonLibs   3 REQUIRED)
find_package(PythonInterp 3 REQUIRED)
find_package(Boost          REQUIRED COMPONENTS python3)

INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})
LINK_LIBRARIES(${Boost_LIBRARIES} ${PYTHON_LIBRARIES})

add_library(gcoder SHARED boost/gcoder.cc )
set_target_properties(gcoder PROPERTIES PREFIX "../python/")
target_include_directories(gcoder PRIVATE gcoder/)
target_link_libraries(gcoder ${Boost_LIBRARIES} GCoder)

add_library(board SHARED boost/board.cc )
set_target_properties(board PROPERTIES PREFIX "../python/")
target_include_directories(board PRIVATE board/)
target_link_libraries(board ${Boost_LIBRARIES} Board)

add_library(logger SHARED boost/logger.cc )
add_dependencies(logger Common)
set_target_properties(logger PROPERTIES PREFIX "../python/")
target_include_directories(logger PRIVATE common/)
target_link_libraries(logger ${Boost_LIBRARIES} Common)

add_library(visual SHARED boost/visual.cc )
set_target_properties(visual PROPERTIES PREFIX "../python/")
target_include_directories(visual PRIVATE visual/)
target_link_libraries(visual ${Boost_LIBRARIES} Visual)

add_library(trigger SHARED boost/trigger.cc)
set_target_properties(trigger PROPERTIES PREFIX "../python/")
target_include_directories(trigger PRIVATE trigger/)
target_link_libraries(trigger ${Boost_LIBRARIES} Trigger)