cmake_minimum_required(VERSION 2.8.3)
project(tf2)

include(conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

find_package(Boost
  REQUIRED COMPONENTS 
    signals 
    system 
    thread 
)

find_package(console_bridge)

add_library(tf2
  # geometry2
  src/cache.cpp
  src/buffer_core.cpp
  src/static_cache.cpp

  # roscpp_core
  src/time.cpp
  src/rate.cpp
  src/duration.cpp
)
target_include_directories(tf2 PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${Boost_INCLUDE_DIRS}
)
target_link_libraries(tf2
  CONAN_PKG::console_bridge
  ${Boost_LIBRARIES}
)

install(TARGETS tf2
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION $<<BOOL:WIN32>:bin,lib>>
)
install(DIRECTORY
    ${CMAKE_CURRENT_SOURCE_DIR}/include/ros
    ${CMAKE_CURRENT_SOURCE_DIR}/include/std_msgs
    ${CMAKE_CURRENT_SOURCE_DIR}/include/geometry_msgs
    ${CMAKE_CURRENT_SOURCE_DIR}/include/tf2_msgs
    ${CMAKE_CURRENT_SOURCE_DIR}/include/tf2
  DESTINATION include
)

# vim: ts=2 sw=2 sts=2 expandtab ft=cmake ffs=unix :
