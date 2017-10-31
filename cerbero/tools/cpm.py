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
import StringIO
import yaml
import shutil

from cerbero.utils import shell
from cerbero.utils import messages as m

def to_unixpath(path):
    if path[1] == ':':
        path = '/%s%s' % (path[0], path[2:])
    return path


def _join(prefix,*items):
    for i in items:
        i= i.strip('/')
        if i and not i=='.':
            prefix +='/'+i
    return prefix

def _rpath(path, prefix):
    '''
    calc the varpath corresponding self.prefix
    '''
    var=os.path.normpath(path).replace('\\','/')
    assert os.path.isabs(path),'''
    path =%s
    prefix =%s
    '''%(path,prefix)
    assert os.path.isabs(prefix),'''
    _rpath prefix should be abs (%s)
    '''%prefix

    #all to unix path
    uprefix = to_unixpath(prefix).replace('\\','/')
    upath   = to_unixpath(var)
    rpath = os.path.relpath(upath.lower(),uprefix.lower())
    n = len(upath)-len(rpath)
    if rpath == '.' or n ==0:
        return ''
        
    if rpath.startswith("..") or n < 0 :
        return None

    return upath[n:].strip('/')


class Error(Exception):
    def __init__(self,message):
        Exception.__init__(self)
        self.message=message   

    
        


class PkgFile(object):



    def __init__(self, root ,mod='r'):
        self._tar = None
        self._hooks =[]
        self._root = root
        

    def open(self, path, mod):
        assert self._tar is None
        self._filename = path
        self._mod = mod

        if mod =='r' and path.endswith('.tar.bz2'):
            mod = 'r:bz2'
        elif mod =='w' and path.endswith('.tar.bz2'):
            mod = 'w:bz2'
        else:
            raise Error("Not support format")

        self._tar = tarfile.open(path,mod)

    def close(self):
        if self._tar:
            self._tar.close()
            self._tar = None


    def _add_hook_handler(self,arcname):
        hooked = False
        path = os.path.join(self._root, arcname )

        for regex,hook in self._hooks:
            if regex.match( arcname ):
                hooked = True

                fobj = open( path ,'rb')
                buf = fobj.read()
                fobj.close()
                
                content , aname = hook(self,arcname,buf)

                if content is not None:
                    self.addfile(content,aname)
                    break

        return hooked

    

    def _extract_hook_handler(self,ti):
        hooked = False
        for regex,hook in self._hooks:
            if regex.match( ti.name ):
                f = self._tar.extractfile(ti)
                buf = f.read()
                f.close()

                hooked = True

                content , aname = hook(self,ti.name,buf)                

                if content is not None:
                    path = os.path.join(self._root,aname)
                    d = os.path.dirname(path)
                    if not os.path.exists(d):
                        os.makedirs(d)
                    f = open(path,'wb')
                    f.write( content )
                    f.close()
                    break
                
        return hooked

    def read(self,arcname):
        ti = self._tar.getmember(arcname)
        if ti:
           f = self._tar.extractfile(ti)
           buf = f.read()
           f.close()
           return buf
        return None

    def add(self, arcname ):
        
        path = os.path.join(self._root,arcname)
        if os.path.isfile(path):
            if not self._add_hook_handler(arcname):                        
                self._tar.add(path, arcname)

        elif os.path.isdir(path):
            #if arcname:
            #    self._tar.add(path,arcname,recursive=False)

            for root, dirs, files in os.walk(path):

                for filename in files:
                    #aname = '%s/%s/%s'%(arcname,middle,filename)
                    fpath = os.path.join(root,filename)
                    aname = _rpath(fpath,self._root)

                    if not self._add_hook_handler(aname):                        
                        self._tar.add(fpath, aname)


    def addfile(self,content, arcname ):

        fobj = StringIO.StringIO(arcname)
        fobj.write(content)
        fobj.seek(os.SEEK_SET,0)
        ti = tarfile.TarInfo(arcname)
        ti.name = arcname
        ti.size = fobj.len

        self._tar.addfile(ti, fobj)
        
        



    def extract(self):
        for m in self._tar.getmembers():
            if not self._extract_hook_handler( m ):
                self._tar.extract(m.name,self._root)



    def addhook(self,regex ,hook):
        self._hooks.append((re.compile(regex),hook))




P_SYMBOL=re.compile(r'\w+')

P_PATH=re.compile(r'(/\w\:[\w/\\]+)|(/\w[\w/]+)')



def _pc_normalize(pkg, arcname,buf):
    lines = buf.splitlines()

    vars ={}#'key','value','lineno'
    flags={}

    PATTERN_VALUE=re.compile(r'^(?P<key>\w+)=(?P<value>.+)')
    PATTERN_FLAG=re.compile(r'^(?P<key>\w+(\.\w+)?):(?P<value>.+)')


    for n in range(len(lines)):
        line = lines[n]

        m = PATTERN_VALUE.match( line )
        if m:
            name = m.group('key')
            value = m.group('value')
            vars[name]={'lineno':n, 'value':value }
            continue
        m = PATTERN_FLAG.match(line)
        if m:
            name = m.group('key')
            value = m.group('value')
            flags[name]={'lineno':n, 'value':value }
            continue
    prefix=vars['prefix']['value']
    prefix_suffix= _rpath(prefix,pkg._root)
    
    root = pkg._root
    if platform.system() == "Windows" and root[0]=='/':
        root = root[1] + ':' + root[2:]

    lines[vars['prefix']['lineno']]='prefix=%s'%root.replace('\\','/')
    vars.pop('prefix')
    for name, val in vars.viewitems():
        v = val['value']
        n = val['lineno']

        if v.startswith('${prefix}'):
            lines[n]='%s=%s'%(name,_join('${prefix}',v[len('${prefix}'):]))
        elif P_PATH.match(v):
            rpath = _rpath( v, prefix )
            lines[n]='%s=%s'%(name,_join('${prefix}',prefix_suffix,rpath))

    

    for flag in ['Libs.private','Cflags']:
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
                    rpath = _rpath( d , prefix )
                    line +=_join(' %s${prefix}'%opt,rpath)
                else:
                    line +=' %s'%field

            lines[lineno] = '%s:%s'%(flag,line)
    return '\n'.join(lines),arcname


def _la_normalize(pkg, arcname,buf):
    lines = buf.splitlines()

    P = re.compile(r"^(?P<key>(libdir|dependency_libs))=\'(?P<value>.+)\'")
    for i in range(len(lines)):
        line = lines[i]
        m = P.match(line)
        if not m :
            continue
        name = m.group('key')
        value  = m.group('value')

        if name == 'libdir':
            val = _rpath(value,pkg._root)
            
            lines[i] = "libdir='%s'"%_join('${prefix}',val)
            
        options=[]

        if name=='dependency_libs':
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
                        d = _rpath( d, pkg._root )
                        if d is None:
                            d = val
                        else:
                            d = _join('${prefix}',d)
                            d = to_unixpath(d)
                    
                    option='%s%s'%(flag , d )
                if option not in options:
                    options.append(option)

            lines[i]="dependency_libs='"
            for opt in options:
                lines[i] +=' %s'%opt
            lines[i] +="'"

    return '\n'.join(lines),arcname















def _pc_extractor( pkg, arcname, buf ):
    P = re.compile(r'^prefix=(?P<value>.+)')
    m = P.match(buf)
    assert m
    start = m.start('value')
    end = m.end('value')

    prefix = pkg._root.replace('\\','/')
    buf = buf[:start] + prefix + buf[end:]
    return buf, arcname


def _get_pkg_name(info):
    """filename of the pcakge"""
    t={'runtime':'','devel':'-devel'}[info['type']]
    i = info.copy()
    if not info.get('prefix',None):
        i['prefix']=''

    if 'runtime' == info.get('type',None):
        i['type']=''
    elif 'devel' == info.get('type',None):
        i['type']='-devel'
        
    return "%(prefix)s%(name)s-%(platform)s-%(arch)s-%(version)s%(type)s" %i

class Desc(object):
    ''' build package description '''

    _properties=['name','platform',
    'arch','version','type','prefix',
    'deps']


    def __init__(self,format='yaml'):
        for name in self._properties:
            setattr(self,name,None)
        setattr(self,'deps',{})


    def from_dict(self,desc):
        for name ,value in desc.viewitems():
            if name in self._properties:
                setattr(self,name,value)
    def to_dict(self):
        desc={}
        for name in self._properties:
            desc[name] =getattr(self,name)
        return desc




    def load(self, document):
        self.from_dict( yaml.load(document) )

    def dump(self,stream=None):
        return yaml.dump( self.to_dict(),stream,
        default_style=False, default_flow_style=False)

    def filename(self,ext='.tar.bz2'):
        i = self.to_dict()
        if 'runtime' == i.get('type','runtime'):
            i['type']=''
        else:
            i['type']='-devel'

        i['prefix']=i.get('prefix','')

        return "%(prefix)s%(name)s-%(platform)s-%(arch)s-%(version)s%(type)s" %i + ext




def Pack(prefix,output_dir, desc, items=['']):

    path = os.path.join(output_dir,desc.filename())

    pkg = PkgFile(prefix)
    pkg.open(path,'w')

    pkg.addfile(desc.dump(),".desc")

    pkg.addhook( r'.*\.pc$',_pc_normalize)
    pkg.addhook( r'.*\.la$',_la_normalize)
    for i in items:
        pkg.add(i)    

    pkg.close()


def filename(info,ext='.tar.bz2'):
    ''' get filename according info '''
    return _get_pkg_name(info) +ext



EX_PATTERN_libdir=re.compile(r"^libdir='(?P<prefix>\$\{prefix\}).*$")
EX_PATTERN_dependency_libs=re.compile(r"^dependency_libs=(?P<value>.*)$")


def _la_extractor( pkg, arcname, buf ):
    lines = buf.splitlines()
    
    to_find_libdir = True
    to_find_dep=True
    for i in range( len(lines)):

        
        line = lines[i]

        if to_find_libdir and EX_PATTERN_libdir.match(line):
            prefix = pkg._root.replace('\\','/')
            lines[i] = line.replace('${prefix}',prefix)
            to_find_libdir = False
            continue
        
        if to_find_dep and EX_PATTERN_dependency_libs.match(line):
            prefix = pkg._root.replace('\\','/')
            if prefix[1]==':':
                prefix = '/%s%s'%(prefix[0],prefix[2:])
            lines[i] = line.replace('${prefix}',prefix)
            to_find_dep = False

    return '\n'.join(lines), arcname

def _noop(pkg,arcname,buf):
    return None,arcname

def Install(prefix, filename):


    pkg = PkgFile(prefix)
    pkg.open(filename,'r')

    content = pkg.read('.desc')
    desc = json.loads(content)
    instd= os.path.join(prefix,'.inst','%(type)s.%(name)s@%(version)s'%desc)
    path = os.path.join(instd,'.desc')
    if not os.path.exists(instd):
        os.makedirs(instd)
    f = open(path,'w')
    f.write(content)
    f.close()

    pkg.addhook( r'.*\.pc$',_pc_extractor)
    pkg.addhook( r'.*\.la$',_la_extractor)
    pkg.addhook( r'^\.desc$',_noop)
    pkg.extract()
    pkg.close()



def load_yaml(location):
    import yaml
    
    
    path = ''
    tmpd=None
    if os.path.exists(location):
        path = location        
    else :
        tmpd = tempfile.mkdtemp()
        path = os.path.join(tmpd,'Build.yaml')
        shell.download( location,path)
    f = open(path,'rb')
    info = yaml.load(f)
    f.close()
    if tmpd:
        shutil.rmtree( tmpd)
    return info

def BuildInstall( prefix, location, cached ):

    binfo = load_yaml(os.path.join(location,'Build.yaml'))

    #install components
    for components in binfo.get('component',{}):
        for name, value in components.viewitems():
            for ptype, comp in value.viewitems():
                filename = value['filename']
                url = os.path.join( location, filename )
                path = url
                if not os.path.exists(url):
                    path = os.path.join(cached,filename)
                    shell.download(url,path)
                m.message('install %s'%filename)

                Install(prefx, path)
    m.message('Install Build done.')

def BBInstall( prefix, location, cached ):
    bbinfo = load_yaml(os.path.join(location,'BB.yaml'))


    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='cpm')
    #parser.add_argument('--pack', action='store_true', help='pack help')
    subparsers = parser.add_subparsers(dest='command',help='sub-command help')

    pack = subparsers.add_parser('pack', help='pack help')
    pack.add_argument("--name", type=str,
                    help="Name of the package to be packed")

    pack.add_argument("--version", type=str,
                    help="Version of the package to be packed")

    pack.add_argument("--platform", type=str, choices=["windows","linux"],
                    help="Platform of the package to be packed")

    pack.add_argument("--arch", type=str, choices=["x86","x86_64"],
                    help="Architecture of the package to be packed")

    pack.add_argument("--type", type=str, choices=["runtime","devel"],
                    default='runtime',
                    help="Type of the package to be packed")

    pack.add_argument("--root-dir", type=str, 
                    help="Source root directory of the package to be packed")


    pack.add_argument("--prefix", type=str, default='',
                    help="Prefix of the package to be packed")

    pack.add_argument("--output-dir", type=str, default='.',
                    help="Output directory of the packed package")


    install = subparsers.add_parser('install', help='install help')
    install.add_argument('--dir', type=str, default='.',
                      help='directory of the package file to be installed.')

    install.add_argument('--package', type=str,
                      help='package to be install.')

    
    args = parser.parse_args()
    if args.command == 'pack':
        info={'name':args.name,
        'version': args.version,
        'platform': args.platform,
        'arch':args.arch,
        'type':args.type,
        'prefix':args.prefix
        }

        Pack(args.root_dir,args.output_dir,info)
        
    elif args.command == 'install':
        Install(args.dir,args.package)