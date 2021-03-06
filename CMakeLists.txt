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
target_compile_features(tf2 PUBLIC cxx_override)
set_target_properties(tf2 PROPERTIES
  CXX_STANDARD 11
  CXX_STANDARD_REQUIRED YES
)
if(BUILD_SHARED_LIBS)
  # Though not really used in the code in this project, this is ROS's custom
  # define used when building shared libs.
  target_compile_definitions(tf2 PUBLIC -DROS_BUILD_SHARED_LIBS)
endif()

if(WIN32)
  set(RUNTIME_DESTINATION bin)
else()
  set(RUNTIME_DESTINATION lib)
endif()
install(TARGETS tf2
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION ${RUNTIME_DESTINATION}
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
