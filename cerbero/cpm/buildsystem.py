# Cerbero Package Manager ,Inspire by ArchLinux Pacman
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



class BuildSystem(object):
    _config =None
    _cookbook = None
    _store = None
    _SDKs=None
    _packages=None

    def __init__(self, config):
        if self._config is None:
            self._config = config
        else:
            assert self.config.arch == config.arch and \
            self.config.platform == config.platform

        assert config or self._config
#        self.config = config
#        self.cookbook = CookBook(config)
#        self.store = PackagesStore(config)
#        self._SDKs={'':set()}
#        self._PACKAGEs={'':set()}
        
        
    def cookbook(self):
        if self._cookbook is None:
            self._cookbook = CookBook(self._config)
        return self._cookbook

    def store(self):
        if self._store is None:
            self._store = PackagesStore(self._config)
        return self._store

    def SDKs(self):
        if self._SDKs is None:
            store = self.store()
            self._SDKs={}
            pkgs={}
            #construct SDK tree first
            for pkg in store.get_packages_list():
                if not isinstance (pkg,SDKPackage):
                    pkgs[pkg.name] = pkg
                    continue
                self._SDKs[pkg.name] = pkg
            if self._packages is None:
                self._packages = pkgs
        return self._SDKs

    def Packages(self):
        if self._packages is None:
            sdk = self.SDKs()
            assert self._packages
        return self._packages

    def get_package_recipes(self,pkg_name, with_deps=False):
        ''' get package recipes '''
        store = self.store()

        deps = store.get_package_deps( pkg_name, False)
        package = store.get_package(pkg_name)
        all = package.recipes_dependencies()
        if not with_deps:
            for pkg in deps:
                r = pkg.recipes_dependencies()
                all = list(set(all).difference(set(r)))
        return all
    def recipe(self,name):
        return self.cookbook().get_recipe(name)

    def recipe_deps(self,name):
        deps={}
        for recipe in self.cookbook().list_recipe_deps(name):
            if recipe.name == name:
                continue
            deps[recipe.name]=recipe.version
        return deps

        








    #def init(self):
#
    #    #construct SDK tree first
    #    for pkg in self.store.get_packages_list():
    #        if not isinstance (pkg,SDKPackage):
    #            continue
    #        deps = self._SDKs.get(pkg.name,set())
    #        for name, required, selected in pkg.packages:
    #            if name not in deps:
    #                deps.add(name)
    #        self._SDKs[pkg.name] =deps
#
    #    for pkg in self.store.get_packages_list():
    #        if isinstance (pkg,SDKPackage):
    #            continue
    #        sdk = self.get_package_sdk(pkg.name)
    #        if sdk is not None:
    #            self._SDKs[sdk].add(pkg.name)
#
#
    #    
#
#
#
#
#
#
#
    #def recipes(self,pkg_name,recursive=False):
    #    ''' get package recipes '''
    #    deps = self.store.get_package_deps( pkg_name, False)
    #    package = self.store.get_package(pkg_name)
    #    all = package.recipes_dependencies()
    #    if not recursive:
    #        for pkg in deps:
    #            r = pkg.recipes_dependencies()
    #            all = list(set(all).difference(set(r)))
    #    return all
#
    #def packages(self,sdk_name='' ):
    #    ''' get sdk packages  '''
    #    return self._SDKs.get(sdk_name,None)
#
    #def SDKs(self,name):
    #    return self._SDKs
#
    #def package(self, name):
    #    return self.store.get_package(name)    
#
    #def get_package_sdk(self,pkg_name):
    #    for name, pkgs in self._SDKs.viewitems():
    #        if pkg_name in pkgs:
    #            return name
    #    return None