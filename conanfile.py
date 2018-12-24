#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, CMake, tools
from conans.model.version import Version


class Tf2Conan(ConanFile):
    name             = 'tf2'
    version          = 'melodic'
    license          = 'Creative Commons Attribution 3.0'
    url              = 'http://wiki.ros.org/tf2'
    description      = 'ROS-independent build of tf2, built by grabbing TF2 files from ros/geometry2/tf2, and supplying the dependencies with files normally installed by the ROS ppa'
    settings         = 'os', 'compiler', 'build_type', 'arch'
    options          = {'shared': [True, False]}
    default_options  = 'shared=True'
    generators       = 'cmake'
    requires = (
        'boost/[>1.60]@conan/stable',
        'console_bridge/0.4.2@ntc/stable',
        'helpers/0.3@ntc/stable',
    )
    options = {
        'shared': [True, False],
    }
    default_options = ('shared=True')
    exports_sources = 'include*', 'src*', 'CMakeLists.txt', 'patches*'

    def config_options(self):
        if 'Visual Studio' == self.settings.compiler:
            # When shared, VS trips over a bunch of undeclared symbols. (Not
            # yet tested with Melodic, this is what happened with indigo
            # though)
            self.options.remove('shared')

    def source(self):
        # Suppress the NO_ERROR conflict, as it appears that ROS doesn't want
        # to https://github.com/ros/geometry2/issues/172
        if 'Visual Studio' == self.settings.compiler:
            if Version(str(self.settings.compiler.version)) < '14':
                tools.replace_in_file(
                    file_path=os.path.join('include', 'tf2_msgs', 'TF2Error.h'),
                    search='  enum',
                    replace='#undef NO_ERROR\n  enum'
                )
            else:
                tools.patch(patch_file='patches/suppress_NO_ERROR.patch')

    def _setup_cmake(self):
        cmake = CMake(self)

        cmake.definitions['BOOST_ROOT:PATH']         = self.deps_cpp_info['boost'].rootpath
        cmake.definitions['BUILD_SHARED_LIBS:BOOL']  = 'TRUE' if 'shared' in self.options and self.options.shared else 'FALSE'

        cmake.definitions['console_bridge_DIR:PATH'] = os.path.join(self.deps_cpp_info['console_bridge'].rootpath, 'lib', 'console_bridge', 'cmake')

        return cmake

    def build(self):
        cmake = self._setup_cmake()
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = self._setup_cmake()
        cmake.configure()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
