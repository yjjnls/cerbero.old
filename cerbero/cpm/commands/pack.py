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

from cerbero.commands import Command, register_command
from cerbero.build.cookbook import CookBook
from cerbero.build.oven import Oven
from cerbero.utils import _, N_, ArgparseArgument
from cerbero.tools.mkpkg import Packager, BuildTree
from cerbero.utils import messages as m
from cerbero.cpm.utils import SHA1
from cerbero.cpm.buildsystem import BuildSystem
from cerbero.cpm.packager import  Description,Component,PkgFile
from cerbero.cpm.packager import  Pack as MakePackage


class Pack(Command):
    doc = N_('Package cerbero components')
    name = 'cpm-pack'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('object', nargs='*',
                    help=_('name of the objects to pack')),

                ArgparseArgument('--type', type=str,
                    default='recipe',choices=['recipe','package','sdk','build-tools'],
                    help=_('type of the moudle')),

                ArgparseArgument('--gen-desc-only', action='store_true',
                    default=False,
                    help=_('generate description file (in yaml format)')),
                    
                ArgparseArgument('--prefix', type=str,
                    default='',
                    help=_('prefix of package file name')),

                ArgparseArgument('--output-dir', type=str,
                    default='.',
                    help=_('directory of package to be output'))
                ]
            
            Command.__init__(self, args)

    def run(self, config, args):
        self.bs = BuildSystem(config)


        if args.type == 'build-tools':
            self._build_tools( config ,args )
            return

        recipes = self._get_recipes(config ,args)

        m.message('totoal %d recipes.'%len(recipes))

        if not args.gen_desc_only:
            i=1
            for name in recipes:
                print '  %3d. %-20s'%(i,name),
                component = Component( config, name)
                component.make( args.prefix,args.output_dir)
                print '   [OK]'
                i +=1
        self._gen_desc_yaml(config,args)
        



    def _get_recipes(self,config,args):
        bs = self.bs

        #bt = self.build_tree
        all=[]
        recipes = args.object
        if args.type == 'package':
            for pkg in args.object:
                all += bs.get_package_recipes(pkg)
            return all

        elif args.type == 'sdk':
            all=[]
            SDKs = bs.SDKs()
            packages = bs.Packages()
            for sdk in args.object:
                for name, required, selected in SDKs[sdk].packages:                    
                    all +=bs.get_package_recipes( name )
            return all
        else:
            return recipes

    def _build_tools(self, config, args):
        bs = self.bs
        sdk = bs.SDKs()
        gst = sdk['gstreamer-1.0']


        #bt = BuildTree(config)
        #pkg = bt.package('gstreamer-1.0')

        assert gst.sdk_version == '1.0'
        
        
        desc = Description()
        desc.from_dict({'name':'build-tools',
        'platform':config.platform,
        'arch':config.arch,
        'version':gst.version,
        'type':'runtime',
        'prefix':'gstreamer-',
        'deps':[]})

        MakePackage(config.build_tools_prefix,args.output_dir,desc )

    def _origin_description(self,config ,args):
        bs = self.bs

        info={}

        if args.type == 'sdk':
            SDKs={}
            for name in args.object:
                sdk = bs.SDKs().get(name)
                SDKs[name]={'version':sdk.version,'package':[]}
                for pkgname, required, selected in sdk.packages:
                    SDKs[name]['package'].append(pkgname)

            info={'SDK':SDKs}

        elif args.type == 'package':
            info={'package':args.object}
                    
        
        return info

    def _gen_desc_yaml(self,config,args):
        from cerbero.tools.cpm import Pack,Desc

        info={
            'platform': config.platform,
            'arch':config.arch,
            'origin': self._origin_description(config,args)
        }

        recipes = self._get_recipes(config,args)
        components={}
        for name in recipes:    
            recipe = self.bs.recipe(name)

            component = components.get(name,{})
            component['version'] = recipe.version

            deps={}

            for ctype in ['runtime','devel']:
                desc = Description()
                desc.name = recipe.name
                desc.version = recipe.version
                desc.platform = config.platform
                desc.arch = config.arch
                desc.type = ctype
                desc.prefix = args.prefix
                      

                filename = desc.filename()
                path = os.path.join(args.output_dir,filename)
                assert os.path.exists(path),'''
                package %s not exists!
                '''%filename
                #dependencies
                
                
                pkg = PkgFile(config.prefix)
                pkg.open( path,'r')
                content = pkg.read('.desc')
                pkg_desc = Description()
                pkg_desc.load( content )
                deps[ctype] = pkg_desc.dependencies
                



                component[ctype]={'filename':filename,
                    'SHA1':SHA1(path)}

            assert 0 == cmp( deps['runtime'] ,deps['devel'] ),'''
            runtime lib diff with devel
            '''
            component['dependencies'] = deps['devel']

            components[name] = component
            
        info['component']= components

        import yaml

        f = open(os.path.join(args.output_dir,'Build.yaml'),'w+')
        data = yaml.dump(info,default_style=False,default_flow_style=False)
        f.write(data)
        f.close()

   


register_command(Pack)
