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
import hashlib

from cerbero.commands import Command, register_command
from cerbero.build.cookbook import CookBook
from cerbero.build.oven import Oven
from cerbero.utils import _, N_, ArgparseArgument
from cerbero.tools.mkpkg import Packager, BuildTree
from cerbero.utils import messages as m
from cerbero.tools import cpm


def SHA1(fineName, block_size=64 * 1024):
  with open(fineName, 'rb') as f:
    sha1 = hashlib.sha1()
    while True:
      data = f.read(block_size)
      if not data:
        break
      sha1.update(data)
    digest = sha1.hexdigest()
    return digest

class MKPkg(Command):
    doc = N_('Make package for modules')
    name = 'mkpkg'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('module', nargs='*',
                    help=_('name of the modules to make')),

                ArgparseArgument('--type', type=str,
                    default='receipe',choices=['receipe','package','sdk','build-tools'],
                    help=_('type of the moudle')),

                ArgparseArgument('--build-desc-only', action='store_true',
                    default=False,
                    help=_('generate (components) build description file (in yaml format)')),
                    
                ArgparseArgument('--prefix', type=str,
                    default='',
                    help=_('prefix of package file name')),

                ArgparseArgument('--output-dir', type=str,
                    default='.',
                    help=_('directory of package to be output')),

                ArgparseArgument('--missing-files', action='store_true',
                    default=False,
                    help=_('prints a list of files installed that are '
                           'listed in the recipe')),
                ArgparseArgument('--dry-run', action='store_true',
                    default=False,
                    help=_('only print commands instead of running them '))]
            if force is None:
                args.append(
                    ArgparseArgument('--force', action='store_true',
                        default=False,
                        help=_('force the build of the recipe ingoring '
                                    'its cached state')))
            if no_deps is None:
                args.append(
                    ArgparseArgument('--no-deps', action='store_true',
                        default=False,
                        help=_('do not build dependencies')))

            self.force = force
            self.no_deps = no_deps
            
            Command.__init__(self, args)

    def run(self, config, args):
        self.build_tree = BuildTree(config)
        self.config = config
        self.args = args

        if args.type == 'build-tools':
            self._build_tools( config ,args )
            return
        receipes = self._get_receipes()

        m.message('totoal %d receipes.'%len(receipes))

        if not self.args.build_desc_only:
            for name in receipes:
                m.message('pack %s'%name)
                pkg = Packager(config,name)
                pkg.make( args.prefix,args.output_dir)


        self._gen_packages_yaml()



        return

    def _get_receipes(self):
        bt = self.build_tree
        receipes = self.args.module
        if self.args.type == 'package':
            all=[]
            for pkg in receipes:
                all +=bt.receipes(pkg)
            return all

        elif self.args.type == 'sdk':
            all=[]
            for sdk in receipes:
                for pkg in bt.packages(sdk):
                    all += bt.receipes(pkg)
            return all
        else:
            return receipes

    def _build_tools(self, config, args):
        bt = BuildTree(config)
        pkg = bt.package('gstreamer-1.0')

        assert pkg.sdk_version == '1.0'
        
        
        info ={'name':'build-tools',
        'platform':config.platform,
        'arch':config.arch,
        'version':pkg.version,
        'type':'runtime',
        'prefix':args.prefix,
        'deps':[] }

        from cerbero.tools.cpm import Pack
        from cerbero.tools.cpm import Desc


        Pack(config.build_tools_prefix,args.output_dir,info )

    def _origin_description(self):
        info={    }

        if self.args.type == 'sdk':
            SDKs={}
            for sdk in self.args.module:
                version = self.build_tree.store.get_package(sdk).version

                SDKs[sdk]=[{'version':version}]
                packages=[]
                for pkg in self.build_tree.packages(sdk):
                    packages.append(pkg)
                SDKs[sdk].append({'packages':packages})
            info['SDK']=SDKs
                    
        
        return info

    def _gen_packages_yaml(self):
        from cerbero.tools.cpm import Pack,Desc

        info={
            'platform': self.config.platform,
            'arch':self.config.arch,
            'origin': self._origin_description()
        }

        receipes = self._get_receipes()
        packages={}
        cookbook = self.build_tree.cookbook
        for name in receipes:    
            receipe = cookbook.get_recipe(name)

            pkg = packages.get(name,{})
            pkg['version'] = receipe.version


            for ptype in ['runtime','devel']:
                desc = Desc()
                desc.name = receipe.name
                desc.version = receipe.version
                desc.platform = self.config.platform
                desc.arch = self.config.arch
                desc.type = ptype
                desc.prefix = self.args.prefix
                      

                filename = desc.filename()
                path = os.path.join(self.args.output_dir,filename)
                assert os.path.exists(path),'''
                package %s not exists!
                '''%filename

                pkg[ptype]={'filename':filename,
                    'SHA1':SHA1(path) }

            packages[receipe.name] = pkg
        info['component']= packages

        import yaml

        f = open(os.path.join(self.args.output_dir,'Build.yaml'),'w+')
        data = yaml.dump(info,default_style=False,default_flow_style=False)
        f.write(data)
        f.close()

   


register_command(MKPkg)
