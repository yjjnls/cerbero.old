# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2012 Andoni Morales Alastruey <ylatuya@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os

from cerbero.config import Platform, Architecture, Distro
from cerbero.utils import shell, to_unixpath, add_system_libs
from cerbero.utils import messages as m
import shutil
import re
from cerbero.build.build import MakefilesBase, modify_environment
from cerbero.build.recipe import BuildSteps
from cerbero.tools import mswin

class AutoCMake (MakefilesBase):
    '''
    Build handler for cmake projects
    '''

    config_sh = 'cmake'
    configure_tpl = '%(config-sh)s -DCMAKE_INSTALL_PREFIX=%(prefix)s '\
                    '-DCMAKE_LIBRARY_OUTPUT_PATH=%(libdir)s '\
                    '-DCMAKE_BUILD_TYPE=%(build_type)s '\
                    '-DCMAKE_CONFIGURATION_TYPES=%(build_type)s '\
                    '-D__AUTOCMAKE__=ON '\
                    '%(options)s '\

    requires_non_src_build = True
    gcc_position_independent_code = True

    VCVARS=None



    def __init__(self):
        MakefilesBase.__init__(self)

        if self.config.target_platform == Platform.WINDOWS:
            self._remove_steps([BuildSteps.GEN_LIBFILES])
            self.VCVARS = mswin.vcvars(2015,self.config.target_arch)

            arch={Architecture.X86:'x86',Architecture.X86_64:'x64'}[self.config.target_arch]

#            self.make = 'msbuild.exe ALL_BUILD.vcxproj //p:Configuration=%s'%self.config.build_type
            #self.make_install = 'msbuild.exe INSTALL.vcxproj //p:Configuration=%s'%self.config.build_type
            #self.make_check = 'msbuild.exe RUN_TESTS.vcxproj //p:Configuration=%s'%self.config.build_type
            #self.make_clean = 'msbuild.exe //t:clean ALL_BUILD.vcxproj //p:Configuration=%s'%self.config.build_type
            self.make = 'cmake --build . --target ALL_BUILD --config %s -- /p:Platform=%s'%(self.config.build_type,arch)
            self.make_install = 'cmake --build . --target INSTALL --config %s -- /p:Platform=%s'%(self.config.build_type,arch)
            self.make_check = 'cmake --build . --target RUN_TESTS --config %s -- /p:Platform=%s'%(self.config.build_type,arch)
            self.make_clean = 'cmake --build . --target ALL_BUILD --config %s -- /t:clean /p:Platform=%s'%(self.config.build_type,arch)

    @modify_environment
    def configure(self):
        if self.config.target_platform != Platform.WINDOWS:
            cc = os.environ.get('CC', 'gcc')
            cxx = os.environ.get('CXX', 'g++')
            cflags = os.environ.get('CFLAGS', '')
            cxxflags = os.environ.get('CXXFLAGS', '')
            os.environ['PKG_CONFIG_PATH'] = os.path.join(self.config.prefix, 'lib', 'pkgconfig')
            
            if self.gcc_position_independent_code:
                cflags += " -fPIC "
                cxxflags += " -fPIC "

        # FIXME: CMake doesn't support passing "ccache $CC"
        if self.config.use_ccache:
            cc = cc.replace('ccache', '').strip()
            cxx = cxx.replace('ccache', '').strip()

        if self.config.target_platform == Platform.WINDOWS:
            if self.config.target_arch == Architecture.X86:
                self.configure_options += ' -G"Visual Studio 14" '
            elif self.config.target_arch == Architecture.X86_64:
                self.configure_options += ' -G"Visual Studio 14 2015 Win64" '

        elif self.config.target_platform == Platform.ANDROID:
            self.configure_options += ' -DCMAKE_SYSTEM_NAME=Linux '


        _autocmake = os.path.abspath( os.path.dirname(__file__)  )
        self.configure_options += '-DCMAKE_MODULE_PATH=%s '%_autocmake




        # FIXME: Maybe export the sysroot properly instead of doing regexp magic
        if self.config.target_platform in [Platform.DARWIN, Platform.IOS]:
            r = re.compile(r".*-isysroot ([^ ]+) .*")
            sysroot = r.match(cflags).group(1)
            self.configure_options += ' -DCMAKE_OSX_SYSROOT=%s' % sysroot

        if self.config.target_platform != Platform.WINDOWS:
            self.configure_options += ' -DCMAKE_C_COMPILER=%s ' % cc
            self.configure_options += ' -DCMAKE_CXX_COMPILER=%s ' % cxx
            self.configure_options += ' -DCMAKE_C_FLAGS="%s"' % cflags
            self.configure_options += ' -DCMAKE_CXX_FLAGS="%s"' % cxxflags
        self.configure_options += ' -DLIB_SUFFIX=%s ' % self.config.lib_suffix
        
        cmake_cache = os.path.join(self.build_dir, 'CMakeCache.txt')
        cmake_files = os.path.join(self.build_dir, 'CMakeFiles')
        if os.path.exists(cmake_cache):
            os.remove(cmake_cache)
        if os.path.exists(cmake_files):
            shutil.rmtree(cmake_files)
        #MakefilesBase.configure(self)
        if not os.path.exists(self.make_dir):
            os.makedirs(self.make_dir)
        #if self.requires_non_src_build:
        #    self.config_sh = '%s .. '%self.config_sh

        if self.config_src_dir != self.make_dir:
            self.configure_options += ' %s '%self.config_src_dir

        prefix= self.config.prefix
        libdir= self.config.libdir


        self._call(self.configure_tpl % {'config-sh': self.config_sh,
            'prefix': prefix,#to_unixpath(self.config.prefix),
            'libdir': libdir,#to_unixpath(self.config.libdir),
            'host': self.config.host,
            'target': self.config.target,
            'build': self.config.build,
            'build_type': self.config.build_type,
            'options': self.configure_options},
            self.make_dir)

    def _clear_cv(self):
        """ clear compile vars """
        cvars=['CC','CFLAGS','LIBRARY_PATH','CXXFLAGS','CC','CXX','LD','CPP',
        'RANLIB','AR','AS','NM','STRIP','WINDRES','RC','DLLTOOL']
        for v in cvars:
            os.environ[v]=''

    def _call(self,cmd,cmd_dir):
        if self.config.target_platform == Platform.WINDOWS:
            self._clear_cv()
            shell.cmd(cmd, cmd_dir)
        else:
            shell.call(cmd, cmd_dir)



    @modify_environment
    def compile(self):        
        self._call(self.make, self.make_dir)

    @modify_environment
    def install(self):
        self._call(self.make_install, self.make_dir)

    @modify_environment
    def clean(self):
        self._call(self.make_clean, self.make_dir)

    @modify_environment
    def check(self):
        if self.make_check:
            self._call(self.make_check, self.build_dir)
