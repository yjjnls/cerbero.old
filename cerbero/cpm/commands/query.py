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
#from cerbero.tools.mkpkg import Packager, BuildTree
from cerbero.utils import messages as m
from cerbero.cpm.utils import SHA1
from cerbero.cpm.buildsystem import BuildSystem
from cerbero.cpm.packager import  Description,Component,PkgFile
from cerbero.cpm.packager import  Pack as MakePackage


class Query(Command):
    doc = N_('Package cerbero components')
    name = 'cpm-query'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('--configvar', type=str,
                    help=_('type of the moudle'))

                ]
            
            Command.__init__(self, args)

    def run(self, config, args):
        if args.configvar:
            if hasattr(config,args.configvar):
                val = getattr(config,args.configvar)
                print '============================================'
                print 'config.%s=%s'%(args.configvar,val)
                print '============================================'
                return
        print 'undefined'

        

register_command(Query)
