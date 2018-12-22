Conan recipe to build ROS's TF2 library.  This script should work on all platforms.

# Introduction

This is designed to be a _ROS Independent_ build of TF2.  It was built by setting up an 18.04 VM, following the ROS install instructions, cloning the [ros/geometry2](https://github.com/ros/geometry2) repository, and copying in the required files from the apt install.

Specifically:
- Followed [these](http://wiki.ros.org/melodic/Installation/Ubuntu) instructions. _e.g._ added the ppa, and installed `ros-melodic-ros-base`
- Cloned [geomtry2]https://github.com/ros/geometry2) at tag `0.6.5` / `39b89b987e1333d39557ad0555c96214cea17dc8`
- Manually copied the `ros`, `geometry_msgs`, `tf2_msgs`, and `std_msgs` includes installed to the system into `include/`
- Re-wrote the `CMakeLists.txt` file
- Authored the `conanfile.txt` to provide boost and `console_bridge`

# Updating Source

If the tf2 source needs to be updated, _e.g._ if the `melodic-develop` is updated, you should be able to clone the `geometry2` repository, filter tf2 out, and pull the updates in.

```sh
cd /tmp
git clone https://github.com/ros/geometry2
cd geometry2
git filter-branch --subdirectory-filter tf2 -- --all

git clone https://github.com/kheaactua/conan-tf2.git
git checkout melodic
git remote add updates file:///tmp/geometry2

git pull --allow-unrelated-histories updates melodic-devel
```
