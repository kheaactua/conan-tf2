import sys, os
from conans import ConanFile
from conans.errors import ConanException


class Tf2Conan(ConanFile):
    name = 'tf2'
    version = 'indigo'
    license = 'Creative Commons Attribution 3.0'
    url = 'http://wiki.ros.org/tf2'
    description = 'tf2 is the second generation of the transform library, which lets the user keep track of multiple coordinate frames over time.'
    settings = 'os', 'compiler', 'build_type', 'arch'
    options = {'shared': [True, False]}
    default_options = 'shared=True'
    generators = 'cmake'
    ros_install_file = 'indigo-tf2-wet.rosinstall'
    requires = (
        'boost/[>1.46]@lasote/stable',
        'console_bridge/indigo@ntc/stable',
        'gtest/[>=1.8.0]@lasote/stable'
    )
    options = {
        'shared': [True, False],
    }

    def configure(self):
        self.options['boost'].shared = self.options.shared
        self.options['gtest'].shared = self.options.shared

    def system_requirements(self):
        pkg_names = 'rosinstall-generator', 'rosdep', 'wstool', 'rosinstall', 'empy'
        if pkg_names:
            self.run('pip install -U %s'%' '.join(pkg_names))

    def source(self):
        cmd =f'rosinstall_generator tf2 --rosdistro "{self.version}" --deps --wet-only --tar > "{self.ros_install_file}"'
        try:
            self.run(cmd)
        except ConanException:
            self.output.error('rosinstall_generated failed. cmd=%s'%cmd)
            sys.exit(-1)

        cmd = f'wstool init -j8 src "{self.ros_install_file}"'
        try:
            self.run(cmd)
        except ConanException:
            self.output.error('wstool failed, restarting it.  cmd=%s'%cmd)

            try:
                self.run('wstool update -j 4 -t src')
            except ConanException:
                self.output.error('wstool failed')
                sys.exit(-1)

    def build(self):
        if 'indigo' == self.deps_cpp_info['console_bridge'].version:
            console_bridge_cmake_path = os.path.join(self.deps_cpp_info['console_bridge'].rootpath, 'share', 'console_bridge', 'cmake')
        else:
            console_bridge_cmake_path = os.path.join(self.deps_cpp_info['console_bridge'].rootpath, 'lib', 'console_bridge', 'cmake')

        args = []
        args.append('-DBOOST_ROOT:PATH=%s'%self.deps_cpp_info['boost'].rootpath)
        args.append('-DBUILD_SHARED_LIBS=%s'%('TRUE' if self.options.shared else 'FALSE'))
        args.append(f'-DCMAKE_BUILD_TYPE:STRING={self.settings.build_type}')
        args.append('-DGTEST_ROOT:PATH=%s'%self.deps_cpp_info['gtest'].rootpath)
        args.append(f'-Dconsole_bridge_DIR:PATH={console_bridge_cmake_path}')
        args.append('-DCONAN_CONSOLE_BRIDGE_ROOT:PATH=%s'%self.deps_cpp_info['console_bridge'].rootpath)

        cmd = 'src/catkin/bin/catkin_make_isolated --install %s'%(' '.join(args))
        self.output.info(f'Running: {cmd}')
        try:
            self.run(cmd)
        except ConanException:
            self.output.error('catkin_make_isolated failed: cmd=%s'%cmd)
            sys.exit(-1)

    def package(self):
        self.copy(pattern='lib*', dst='lib', src=os.path.join('install_isolated', 'lib'))
        self.copy(pattern='*.h',  dst='include', src=os.path.join('install_isolated', 'include'))

    def package_info(self):
        pass

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
