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

import platform
import re
from cerbero.utils import to_unixpath
from cerbero.cpm.utils import path_join,relpath
from cerbero.cpm import PkgFileProcessor

P_PATH=re.compile(r'(/\w\:[\w/\\]+)|(/\w[\w/]+)')

class Normalizer(PkgFileProcessor):
    PATTERN_VALUE=re.compile(r'^(?P<key>\w+)=(?P<value>.+)')
    PATTERN_FLAG=re.compile(r'^(?P<key>\w+(\.\w+)?):(?P<value>.+)')


    def __init__(self,root_dir):
        PkgFileProcessor.__init__(self,root_dir)


    def process(self,arcname, content):
        lines = content.splitlines()
        element= self._get_pc_elements(lines)
        self._process_vars( lines, element['var'])
        self._process_flags( lines, element['flag'])
        return '\n'.join(lines)



    def _get_pc_elements(self,lines):
        
        vars ={}#'key','value','lineno'
        flags={}

        for n in range(len(lines)):
            line = lines[n]

            m = self.PATTERN_VALUE.match( line )
            if m:
                name = m.group('key')
                value = m.group('value')
                vars[name]={'lineno':n, 'value':value }
                continue
            m = self.PATTERN_FLAG.match(line)
            if m:
                name = m.group('key')
                value = m.group('value')
                flags[name]={'lineno':n, 'value':value }
                continue
        return {'var':vars,'flag':flags}

    def _process_vars(self,lines,vars):

        prefix=vars['prefix']['value']
        prefix_suffix= relpath(prefix,self.rootd)
        
        root = self.rootd
        if platform.system() == "Windows" and root[0]=='/':
            root = root[1] + ':' + root[2:]

        lines[vars['prefix']['lineno']]='prefix=%s'%root.replace('\\','/')
        vars.pop('prefix')
        for name, val in vars.viewitems():
            v = val['value']
            n = val['lineno']

            if v.startswith('${prefix}'):
                lines[n]='%s=%s'%(name,path_join('${prefix}',v[len('${prefix}'):]))
            elif P_PATH.match(v):
                rpath = relpath( v, prefix )
                lines[n]='%s=%s'%(name,path_join('${prefix}',prefix_suffix,rpath))

    def _process_flags(self,lines,flags, flaglist=['Libs.private','Cflags']):
        for flag in flaglist:
            if flags.has_key(flag):
                val = flags[flag]['value']
                lineno = flags[flag]['lineno']
                line=''
                fields =val.split()
                for field in fields:
                    opt = field[:2]
                    if opt in ['-L','-I']:
                        d = field[2:]
                        if d.startswith('${'):
                            line +=' %s'%field
                            continue
                        rpath = relpath( d , self.rootd )
                        line +=path_join(' %s${prefix}'%opt,rpath)
                    else:
                        line +=' %s'%field

                lines[lineno] = '%s:%s'%(flag,line)


class Extractor(PkgFileProcessor):
    P = re.compile(r'^prefix=(?P<value>.+)')

    def __init__(self, root_dir):
        PkgFileProcessor.__init__(self,root_dir)


    def process(self, arcname, content):
        lines = content.splitlines()
        n = 0
        for i in range( len(lines) ):
            line = lines[i]
            m = self.P.match(line)
            if m :
                start = m.start('value')
                end = m.end('value')
                prefix = self.rootd.replace('\\','/')
                lines[i] = line[:start] + prefix + line[end:]
                return "\n".join(lines)
        assert None,"Not found prefix in %s"%arcname

        return content


#def _pc_extractor( pkg, arcname, buf ):
#    P = re.compile(r'^prefix=(?P<value>.+)')
#    m = P.match(buf)
#    assert m
#    start = m.start('value')
#    end = m.end('value')
#
#    prefix = pkg._root.replace('\\','/')
#    buf = buf[:start] + prefix + buf[end:]
#    return buf, arcname
   

#def PCNormalizer(Normalizer):
#
#    def __init__(self,root_dir):
#        PCNormalizer.__init__(self,root_dir)
#
#    def process(self,arcname,content):
#        lines = content.splitlines()
#        element= get_pc_elements(lines)
#        
#
#
#    def _get_elements(self,lines):
#        vars ={}#'key','value','lineno'
#        flags={}
#
#        for n in range(len(lines)):
#        line = lines[n]
#
#        m = self.PATTERN_VALUE.match( line )
#        if m:
#            name = m.group('key')
#            value = m.group('value')
#            vars[name]={'lineno':n, 'value':value }
#            continue
#        m = PATTERN_FLAG.match(line)
#        if m:
#            name = m.group('key')
#            value = m.group('value')
#            flags[name]={'lineno':n, 'value':value }
#            continue
#        return vars,flags
#    
#
#
#
#
#
#def _pc_normalize(pkg, arcname,buf):
#    lines = buf.splitlines()
#
#    vars ={}#'key','value','lineno'
#    flags={}
#
#    PATTERN_VALUE=re.compile(r'^(?P<key>\w+)=(?P<value>.+)')
#    PATTERN_FLAG=re.compile(r'^(?P<key>\w+(\.\w+)?):(?P<value>.+)')
#
#
#    for n in range(len(lines)):
#        line = lines[n]
#
#        m = PATTERN_VALUE.match( line )
#        if m:
#            name = m.group('key')
#            value = m.group('value')
#            vars[name]={'lineno':n, 'value':value }
#            continue
#        m = PATTERN_FLAG.match(line)
#        if m:
#            name = m.group('key')
#            value = m.group('value')
#            flags[name]={'lineno':n, 'value':value }
#            continue
#    prefix=vars['prefix']['value']
#    prefix_suffix= _rpath(prefix,pkg._root)
#    
#    root = pkg._root
#    if platform.system() == "Windows" and root[0]=='/':
#        root = root[1] + ':' + root[2:]
#
#    lines[vars['prefix']['lineno']]='prefix=%s'%root.replace('\\','/')
#    vars.pop('prefix')
#    for name, val in vars.viewitems():
#        v = val['value']
#        n = val['lineno']
#
#        if v.startswith('${prefix}'):
#            lines[n]='%s=%s'%(name,_join('${prefix}',v[len('${prefix}'):]))
#        elif P_PATH.match(v):
#            rpath = _rpath( v, prefix )
#            lines[n]='%s=%s'%(name,_join('${prefix}',prefix_suffix,rpath))
#
#    
#
#    for flag in ['Libs.private','Cflags']:
#        if flags.has_key(flag):
#            val = flags[flag]['value']
#            lineno = flags[flag]['lineno']
#            line=''
#            fields =val.split()
#            for field in fields:
#                opt = field[:2]
#                if opt in ['-L','-I']:
#                    d = field[2:]
#                    if d.startswith('${'):
#                        line +=' %s'%field
#                        continue
#                    rpath = _rpath( d , prefix )
#                    line +=_join(' %s${prefix}'%opt,rpath)
#                else:
#                    line +=' %s'%field
#
#            lines[lineno] = '%s:%s'%(flag,line)
#    return '\n'.join(lines),arcname