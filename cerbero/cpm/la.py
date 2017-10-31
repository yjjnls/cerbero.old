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
import re

from cerbero.utils import to_unixpath
from cerbero.cpm.utils import path_join,relpath
from cerbero.cpm import PkgFileProcessor

class Normalizer(PkgFileProcessor):
    P_libdir = re.compile(r"^(?P<key>libdir)=\'(?P<value>.+)\'")
    P_dependency_libs = re.compile(r"^(?P<key>dependency_libs)=\'(?P<value>.+)\'")



    def __init__(self,root_dir):
        PkgFileProcessor.__init__(self,root_dir)

    def process(self,arcname, content):
        lines = content.splitlines()
        self._libdir( lines)
        self._dependency_libs( lines)
        return '\n'.join(lines)

    def _libdir(self,lines):
        for i in range(len(lines)):
            line = lines[i]
            m = self.P_libdir.match(line)
            if not m :
                continue
            value  = m.group('value')
            val = relpath(value,self.rootd)
            
            lines[i] = "libdir='%s'"%path_join('${prefix}',val)

    def _dependency_libs(self,lines):
        for i in range(len(lines)):
            line = lines[i]
            m = self.P_dependency_libs.match(line)
            if not m : continue
            value  = m.group('value')

            options=[]
            new_val = ''
            for val in value.split():
                flag=''
                if val[0] == '-':
                    flag= val[:2]
                    val = val[2:]

                option='%s%s'%(flag , val )
                if flag in ['','-L','-R']:
                    d = val.lstrip('=')
                    if os.path.isabs(d):
                        d = relpath( d, self.rootd )
                        if d is None:
                            d = val
                        else:
                            d = path_join('${prefix}',d)
                            d = to_unixpath(d)
                    
                    option='%s%s'%(flag , d )
                if option not in options:
                    options.append(option)

            lines[i]="dependency_libs='"
            for opt in options:
                lines[i] +=' %s'%opt
            lines[i] +="'"

class Extractor(PkgFileProcessor):
    EX_PATTERN_libdir=re.compile(r"^libdir='(?P<prefix>\$\{prefix\}).*$")
    EX_PATTERN_dependency_libs=re.compile(r"^dependency_libs=(?P<value>.*)$")


    def __init__(self,root_dir):
        PkgFileProcessor.__init__(self,root_dir)


    def process(self, arcname, content):
        lines = content.splitlines()
        self._replace_prefix(lines)
        return '\n'.join(lines)

    def _replace_prefix(self,lines):
        to_find_libdir = True
        to_find_dep=True
        for i in range( len(lines)):

            
            line = lines[i]

            if to_find_libdir and self.EX_PATTERN_libdir.match(line):
                prefix = self.rootd.replace('\\','/')
                lines[i] = line.replace('${prefix}',prefix)
                to_find_libdir = False
                continue
            
            if to_find_dep and self.EX_PATTERN_dependency_libs.match(line):
                prefix = self.rootd.replace('\\','/')
                if prefix[1]==':':
                    prefix = '/%s%s'%(prefix[0],prefix[2:])
                lines[i] = line.replace('${prefix}',prefix)
                to_find_dep = False



#def _la_extractor( pkg, arcname, buf ):
#    lines = buf.splitlines()
#    
#    to_find_libdir = True
#    to_find_dep=True
#    for i in range( len(lines)):
#
#        
#        line = lines[i]
#
#        if to_find_libdir and EX_PATTERN_libdir.match(line):
#            prefix = pkg._root.replace('\\','/')
#            lines[i] = line.replace('${prefix}',prefix)
#            to_find_libdir = False
#            continue
#        
#        if to_find_dep and EX_PATTERN_dependency_libs.match(line):
#            prefix = pkg._root.replace('\\','/')
#            if prefix[1]==':':
#                prefix = '/%s%s'%(prefix[0],prefix[2:])
#            lines[i] = line.replace('${prefix}',prefix)
#            to_find_dep = False
#
#    return '\n'.join(lines), arcname


#def _la_normalize(pkg, arcname,buf):
#    lines = buf.splitlines()
#
#    P = re.compile(r"^(?P<key>(libdir|dependency_libs))=\'(?P<value>.+)\'")
#    for i in range(len(lines)):
#        line = lines[i]
#        m = P.match(line)
#        if not m :
#            continue
#        name = m.group('key')
#        value  = m.group('value')
#
#        if name == 'libdir':
#            val = _rpath(value,pkg._root)
#            
#            lines[i] = "libdir='%s'"%_join('${prefix}',val)
#            
#        options=[]
#
#        if name=='dependency_libs':
#            new_val = ''
#            for val in value.split():
#                flag=''
#                if val[0] == '-':
#                    flag= val[:2]
#                    val = val[2:]
#
#                option='%s%s'%(flag , val )
#                if flag in ['','-L','-R']:
#                    d = val.lstrip('=')
#                    if os.path.isabs(d):
#                        d = _rpath( d, pkg._root )
#                        if d is None:
#                            d = val
#                        else:
#                            d = _join('${prefix}',d)
#                            d = to_unixpath(d)
#                    
#                    option='%s%s'%(flag , d )
#                if option not in options:
#                    options.append(option)
#
#            lines[i]="dependency_libs='"
#            for opt in options:
#                lines[i] +=' %s'%opt
#            lines[i] +="'"
#
#    return '\n'.join(lines),arcname