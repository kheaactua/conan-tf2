#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import sys, os, glob, platform
from conans import ConanFile, tools, VisualStudioBuildEnvironment
from conans.errors import ConanException


class Tf2Conan(ConanFile):
    name = 'tf2'
    version = 'indigo'
    license = 'Creative Commons Attribution 3.0'
    url = 'http://wiki.ros.org/tf2'
    description = 'tf2 is the second generation of the transform library, which lets the user keep track of multiple coordinate frames over time.'
    settings = 'os', 'compiler', 'build_type', 'arch', 'arch_build'
    options = {'shared': [True, False]}
    default_options = 'shared=True'
    generators = 'cmake'
    ros_install_file = 'indigo-tf2-wet.rosinstall'
    requires = (
        'boost/[>1.46]@ntc/stable',
        'console_bridge/indigo@ntc/stable',
        'gtest/[>=1.8.0]@bincrafters/stable',
        'helpers/0.2@ntc/stable',
    )
    options = {
        'shared': [True, False],
        'fPIC':   [True, False],
    }
    default_options = ('shared=True', 'fPIC=True')

    def system_requirements(self):
        pkg_names = 'rosinstall-generator', 'rosdep', 'wstool', 'rosinstall', 'empy'
        if pkg_names:
            self.run('pip install -U %s'%' '.join(pkg_names))

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            self.options.remove('fPIC')
        if 'Windows' == platform.system():
            self.options.remove('shared')

    def configure(self):
        if 'shared' in self.options:
            self.options['boost'].shared = self.options.shared
        if self.settings.compiler != "Visual Studio":
            self.options['boost'].fPIC = self.options['boost'].shared

    def source(self):
        if 'VIRTUAL_ENV' in os.environ:
            python_bin_path = os.path.join(os.environ['VIRTUAL_ENV'], 'Scripts' if 'Windows' == platform.system() else 'bin')
        else:
            self.output.warn('This script was written to be run in python\'s virtualenv, running outside of a virtualenv might result in difficulty locating the ROS python tools (such as rosinstall_generator')
            python_bin_path = '/usr/bin'

        cmd =f'python {python_bin_path}/rosinstall_generator tf2 --rosdistro "{self.version}" --deps --wet-only --tar > "{self.ros_install_file}"'
        try:
            self.run(cmd)
        except ConanException as e:
            self.output.error('rosinstall_generated failed. cmd=%s\nError: %s'%(cmd, e))
            if os.path.exists(self.ros_install_file):
                with open(self.ros_install_file, 'r') as content_file: content = content_file.read()
                self.output.error('ROS install file contents:\n%s'%content)
            else:
                self.output.error('ROS install file "%s" was not created'%self.ros_install_file)
            sys.exit(-1)

        if 'Linux' == platform.system():
            ncors = tools.cpu_count()
        else:
            # Seems to work better...
            ncors = 1

        cmd = f'python {python_bin_path}/wstool init -j {ncors} src "{self.ros_install_file}"'
        try:
            self.run(cmd)
        except ConanException:
            self.output.error('wstool failed, restarting it.  cmd=%s'%cmd)

            try:
                self.run(f'python {python_bin_path}/wstool update -j {ncors} -t src')
            except ConanException as e:
                self.output.error('wstool failed: %s'%e)
                sys.exit(-1)

        # If we're using MSVC, a env.bat file will be generated rather than a
        # env.sh, update the code to handle this.  The code injected tests for
        # platform though, not compiler, so maybe it should be hard set to
        # env.bat if conan is using MSVC?
        tools.replace_in_file(
            file_path=os.path.join('src', 'catkin', 'python', 'catkin', 'builder.py'),
            search="'env.sh'",
            replace="'env.bat' if 'Windows' == platform.system() else 'env.sh'"
        )

        # Remove code that would otherwise be removed by macros.h, but isn't
        # include here for some reason
        for f in [os.path.join('src', 'geometry2', 'tf2', 'include', 'tf2', 'LinearMath', p) for p in ['Matrix3x3.h', 'Quaternion.h']]:
            tools.replace_in_file(
                file_path=f,
                search='__attribute__((deprecated))',
                replace=''
            )

        if 'Windows' == platform.system():
            # Modify template to remove NO_ERROR name collision with Windows
            tools.replace_in_file(
                file_path=os.path.join('src', 'gencpp', 'scripts', 'msg.h.template'),
                search='#include <ros/message_operations.h>',
                replace='#include <ros/message_operations.h>\n\n\n#ifdef _WIN32\n#undef NO_ERROR\n#endif\n\n'
            )

    def build(self):
        if 'indigo' == self.deps_cpp_info['console_bridge'].version:
            console_bridge_cmake_path = os.path.join(self.deps_cpp_info['console_bridge'].rootpath, 'share', 'console_bridge', 'cmake')
        else:
            console_bridge_cmake_path = os.path.join(self.deps_cpp_info['console_bridge'].rootpath, 'lib', 'console_bridge', 'cmake')

        args = []
        args.append('-DBOOST_ROOT:PATH=%s'%self.deps_cpp_info['boost'].rootpath)
        args.append('-DBUILD_SHARED_LIBS:BOOL=%s'%('TRUE' if 'shared' in self.options and self.options.shared else 'FALSE'))
        args.append(f'-DCMAKE_BUILD_TYPE:STRING={self.settings.build_type}')
        args.append('-DGTEST_ROOT:PATH=%s'%self.deps_cpp_info['gtest'].rootpath)
        args.append(f'-Dconsole_bridge_DIR:PATH={console_bridge_cmake_path}')
        args.append('-DCONAN_CONSOLE_BRIDGE_ROOT:PATH=%s'%self.deps_cpp_info['console_bridge'].rootpath)
        args.append(f'-DCMAKE_INSTALL_PREFIX={self.package_folder}')
        args.append('--use-ninja')

        if self.settings.get_safe('arch').startswith('arm'):
            args.append('-DRT_LIBRARY=%s'%os.path.join(os.environ['TOOLCHAIN_ROOT'], 'libc', 'usr', 'lib', 'librt.so'))

        if self.settings.compiler == "Visual Studio":
            from platform_helpers import adjustPath
            for f in ['cpp_common', 'genmsg', 'roscpp_traits', 'std_msgs', 'geometry_msgs', 'message_generation']:
                args.append('-D%s_DIR=%s'%(f, adjustPath(os.path.join(self.package_folder, 'share', f, 'cmake'))))
            args.append('-DCMAKE_PREFIX_PATH=%s'%adjustPath(self.package_folder))
            env_build = VisualStudioBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                vcvars = tools.vcvars_command(self.settings)
                cmd = '%s && python src/catkin/bin/catkin_make_isolated --install %s'%(vcvars, ' '.join(args))
                self.output.info(f'Running: {cmd}')
                self.run(cmd)
        else:
            cmd = 'src/catkin/bin/catkin_make_isolated --install %s'%(' '.join(args))
            self.output.info(f'Running: {cmd}')
            self.run(cmd)

    def package(self):
        from platform_helpers import adjustPath

        # The pkg-config variables are full of absolute paths.
        p_files = glob.glob(os.path.join(self.package_folder, 'lib', 'pkgconfig', '*.pc'))
        for f in p_files:
            self.output.info('Modifying %s'%f)

            tools.replace_in_file(
                file_path=f,
                search=adjustPath(self.package_folder),
                replace=r'${prefix}',
                strict=False,
            )

            if 'Linux' == platform.system() and os.path.basename(f) in ['cpp_common.pc', 'tf2.pc', 'rostime.pc']:
                # Small bug I saw
                tools.replace_in_file(file_path=f, search=r'-l:', replace=r'-l', strict=False)

            if os.path.basename(f) in ['cpp_common.pc', 'tf2.pc']:
                tools.replace_in_file(
                    file_path=f,
                    search=adjustPath(self.deps_cpp_info['console_bridge'].rootpath),
                    replace=r'${PKG_CONFIG_CONSOLE_BRIDGE_PREFIX}',
                    strict=False
                )

        self.copy(pattern='*.pc',  dst='lib/pkgconfig', src=os.path.join('install_isolated', 'lib', 'pkgconfig'))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        # Populate the pkg-config environment variables
        with tools.pythonpath(self):
            from platform_helpers import adjustPath, appendPkgConfigPath

            pkgs = ['catkin', 'genmsg', 'gencpp', 'genlisp', 'genpy', 'cpp_common', 'message_generation', 'message_runtime', 'roscpp_traits', 'rostime', 'roscpp_serialization', 'std_msgs', 'actionlib_msgs', 'geometry_msgs', 'tf2_msgs', 'tf2']
            for p in pkgs:
                setattr(self.env_info, 'PKG_CONFIG_%s_PREFIX'%p.upper(), adjustPath(self.package_folder))

            appendPkgConfigPath(adjustPath(os.path.join(self.package_folder, 'lib', 'pkgconfig')), self.env_info)

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
