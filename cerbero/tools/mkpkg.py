# mkpkg - CPM packager ,Inspire by ArchLinux and its Pacman
# Copyright (C) 2017 Mingyi Zhang <mingyi.z@outlook.com>
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
import sys
import re
import tempfile
import platform
import tarfile
import json    

from cerbero.build.cookbook import CookBook
from cerbero.tools.cpm import Pack,Desc
from cerbero.packages.packagesstore import PackagesStore
from cerbero.packages.package import SDKPackage
from cerbero.utils import messages as m

class Packager(object):


    def __init__( self, config ,name):
        self.config  = config        
        self.name = name
        self.cookbook = CookBook(self.config)
        self.receipe = self.cookbook.get_recipe(name)
        self.desc = Desc()
        self.desc.name = self.name
        self.desc.platform = self.config.platform
        self.desc.arch = self.config.arch
        self.desc.version = self.receipe.version
    
        self.desc.deps=self._deps()


    def _deps(self):
        deps={}
        runtimes = self.cookbook._runtime_deps()
        rdeps = self.cookbook.list_recipe_deps(self.name)
        for receipe in rdeps:
            if self.name == receipe.name or receipe.name in runtimes:
                continue
            deps[receipe.name]=receipe.version
        return deps

    def _mkruntime(self,prefix,output_dir):

        items=[]
        for i in self.receipe.dist_files_list():
            path = os.path.join(self.config.prefix,i )
            if os.path.exists(path):
                items.append(i)

        self.desc.prefix = prefix
        self.desc.type = 'runtime'

        Pack(self.config.prefix,output_dir,self.desc ,items)
        
    def _mkdevel(self,prefix,output_dir):

        items=[]
        for i in self.receipe.devel_files_list():
            path = os.path.join(self.config.prefix,i )
            if os.path.exists(path):
                items.append(i)

        self.desc.prefix = prefix
        self.desc.type = 'devel'

        Pack(self.config.prefix,output_dir,self.desc ,items)

    def make(self,prefix='',output_dir='.'):        
        odir = os.path.abspath( output_dir)
        self._mkruntime(prefix,output_dir)
        self._mkdevel(prefix,output_dir)





class BuildTree(object):

    def __init__(self, config):
        self.config = config
        self.cookbook = CookBook(config)
        self.store = PackagesStore(config)
        self._SDKs={'':set()}
        self._PACKAGEs={'':set()}
        
        self.init()



    def init(self):

        #construct SDK tree first
        for pkg in self.store.get_packages_list():
            if not isinstance (pkg,SDKPackage):
                continue
            deps = self._SDKs.get(pkg.name,set())
            for name, required, selected in pkg.packages:
                if name not in deps:
                    deps.add(name)
            self._SDKs[pkg.name] =deps

        for pkg in self.store.get_packages_list():
            if isinstance (pkg,SDKPackage):
                continue
            sdk = self.get_package_sdk(pkg.name)
            if sdk is not None:
                self._SDKs[sdk].add(pkg.name)


        







    def receipes(self,pkg_name,recursive=False):
        ''' get package receipes '''
        deps = self.store.get_package_deps( pkg_name, False)
        package = self.store.get_package(pkg_name)
        all = package.recipes_dependencies()
        if not recursive:
            for pkg in deps:
                r = pkg.recipes_dependencies()
                all = list(set(all).difference(set(r)))
        return all

    def packages(self,sdk_name='' ):
        ''' get sdk packages  '''
        return self._SDKs.get(sdk_name,None)

    def SDKs(self,name):
        return self._SDKs

    def package(self, name):
        return self.store.get_package(name)    

    def get_package_sdk(self,pkg_name):
        for name, pkgs in self._SDKs.viewitems():
            if pkg_name in pkgs:
                return name
        return None


