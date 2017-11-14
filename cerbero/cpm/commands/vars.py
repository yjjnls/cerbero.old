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
from cerbero.utils import messages as m
from cerbero.cpm.utils import SHA1
from cerbero.cpm.buildsystem import BuildSystem
from cerbero.cpm.packager import  Description,Component,PkgFile
from cerbero.cpm.packager import  Pack as MakePackage

_ARRARY_TMPL='''
%(name)s=(
%(items)s
)
'''

class Variable(Command):
    doc = N_('Package cerbero components')
    name = 'cpm-vars'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('--filename', type=str,
                    help=_('filename of the shell vars'))

                ]
            
            Command.__init__(self, args)

    def run(self, config, args):
        self.config=config
        self.bs = BuildSystem(config)
        self.f  = open(args.filename,'w+')
        self._config()
        self._pkgver()
        self.f.close()

    def _config(self):
        
        vars=[]
        for prop in self.config._properties:
            var =getattr(self.config,prop)
            if var is None:
                var=''
            if not isinstance( var, str):
                continue

            vars.append("%s '%s' "%(prop,var))

        self.f.write(_ARRARY_TMPL%{
            'name':'__CERBERO_CONFIG',
            'items':'\n'.join(vars)
        })
            
        return vars

    def _pkgver(self):
        store=self.bs.store()
        cookbook = self.bs.cookbook()
        packages = self.bs.Packages()
        vars=[]
        for name in packages:
            pkg = store.get_package(name)
            
            vars.append( "%s '%s'"%(name,pkg.version ))
        for name ,sdk in self.bs.SDKs().viewitems():
            vars.append( "%s '%s'"%(name,sdk.version ))

        self.f.write(_ARRARY_TMPL%{
            'name':'__CERBERO_PACKAGE',
            'items':"\n".join(vars)
        })



        

register_command(Variable)

#export cerbero 