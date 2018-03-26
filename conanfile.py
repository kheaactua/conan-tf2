import sys, os, glob
from conans import ConanFile, tools
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
        'boost/[>1.46]@ntc/stable',
        'console_bridge/indigo@ntc/stable',
        'gtest/[>=1.8.0]@lasote/stable',
        'helpers/[>=0.2]@ntc/stable',
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

    def build_requirements(self):
        if 'Linux' == self.settings.os:
            self.build_requires('pkg-config/0.29.2@ntc/stable')

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

    def configure(self):
        self.options['boost'].shared = self.options.shared
        if self.settings.compiler != "Visual Studio":
            self.options['boost'].fPIC = self.options['boost'].shared

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
        args.append('-DBUILD_SHARED_LIBS:BOOL=%s'%('TRUE' if self.options.shared else 'FALSE'))
        args.append(f'-DCMAKE_BUILD_TYPE:STRING={self.settings.build_type}')
        args.append('-DGTEST_ROOT:PATH=%s'%self.deps_cpp_info['gtest'].rootpath)
        args.append(f'-Dconsole_bridge_DIR:PATH={console_bridge_cmake_path}')
        args.append('-DCONAN_CONSOLE_BRIDGE_ROOT:PATH=%s'%self.deps_cpp_info['console_bridge'].rootpath)

        if self.settings.get_safe('arch').startswith('arm'):
            args.append('-DRT_LIBRARY=%s'%os.path.join(os.environ['TOOLCHAIN_ROOT'], 'libc', 'usr', 'lib', 'librt.so'))

        cmd = 'src/catkin/bin/catkin_make_isolated --install %s'%(' '.join(args))
        self.output.info(f'Running: {cmd}')
        try:
            self.run(cmd)
        except ConanException:
            self.output.error('catkin_make_isolated failed: cmd=%s'%cmd)
            sys.exit(-1)

    def package(self):
        self.copy(pattern='lib*',  dst='lib', src=os.path.join('install_isolated', 'lib'))
        self.copy(pattern='*.h',   dst='include', src=os.path.join('install_isolated', 'include'))

        # The pkg-config variables are full of absolute paths.
        p_files = glob.glob(os.path.join(self.build_folder, 'install_isolated', 'lib', 'pkgconfig', '*.pc'))
        for f in p_files:
            self.output.info('Modifying %s'%f)

            try:
                tools.replace_in_file(
                    file_path=f,
                    search=os.path.join(self.build_folder, 'install_isolated'),
                    replace=r'${prefix}'
                )
            except: pass

            try:
                tools.replace_in_file(file_path=f, search=r'-l:', replace=r'-l') # Small bug I saw
            except: pass

            try:
                tools.replace_in_file(
                    file_path=f,
                    search=self.deps_cpp_info['console_bridge'].rootpath,
                    replace=r'${PKG_CONFIG_CONSOLE_BRIDGE_PREFIX}'
                )
            except: pass

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
