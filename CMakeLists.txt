cmake_minimum_required(VERSION 2.8.3)
project(tf2)

set(boost_DIR /home/vagrant/.conan/data/boost/1.66.0/conan/stable/package/f13b8707a96902c3870d1d62327acbc46ec72985)
set(BOOST_ROOT ${boost_DIR})
find_package(Boost
  REQUIRED COMPONENTS 
    signals 
    system 
    thread 
)

set(console_bridge_DIR /home/vagrant/.conan/data/console_bridge/master/ntc/stable/package/e5085da903678208850391bc46c78941136095c9/lib/console_bridge/cmake)
find_package(console_bridge)


# CPP Libraries
add_library(tf2
  src/cache.cpp
  src/buffer_core.cpp
  src/static_cache.cpp
)
target_include_directories(tf2 PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(tf2
  ${Boost_LIBRARIES}
  ${catkin_LIBRARIES}
  ${console_bridge_LIBRARIES}
)

install(TARGETS tf2
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION $<<BOOL:WIN32>:bin,lib>>
)

# vim: ts=2 sw=2 sts=2 expandtab ft=cmake ffs=unix :
