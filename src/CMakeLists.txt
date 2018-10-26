INCLUDE_DIRECTORIES(gcoder/ session/ board/)

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

