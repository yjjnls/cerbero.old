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

from cerbero.utils import shell, to_unixpath
from cerbero.utils import messages as m
from cerbero.cpm import pc ,la
from cerbero.cpm.buildsystem import BuildSystem
from cerbero.cpm.utils import relpath

class Description(object):
    ''' Component description '''

    _properties=['name','platform',
    'arch','version','type','prefix',
    'dependencies']


    def __init__(self,format='yaml'):
        for name in self._properties:
            setattr(self,name,None)
        setattr(self,'dependencies',{})


    def from_dict(self,desc):
        for name ,value in desc.viewitems():
            if name in self._properties:
                setattr(self,name,value)

    def to_dict(self):
        desc={}
        for name in self._properties:
            desc[name] =getattr(self,name)
        return desc

    def from_recipe(self,config ,name):
        pass




    def load(self, document):
        import yaml
        self.from_dict( yaml.load(document) )

    def dump(self,stream=None):
        import yaml
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


class PkgFile(object):



    def __init__(self, root ,mod='r'):
        self._tar = None
        self._hooks =[]
        self._root = root
        self.extract_list=[]
        

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
                content = fobj.read()
                fobj.close()
                
                content  = hook.process( arcname, content)

                if content:
                    self.addfile(content,arcname)
                break

        return hooked

    

    def _extract_hook_handler(self,ti):
        hooked = False
        for regex,hook in self._hooks:
            if regex.match( ti.name ):
                f = self._tar.extractfile(ti)
                content = f.read()
                f.close()

                hooked = True
                arcname = ti.name

                content =hook.process( arcname, content)

                if content:
                    path = os.path.join(self._root,arcname)
                    d = os.path.dirname(path)
                    if not os.path.exists(d):
                        os.makedirs(d)
                    f = open(path,'wb')
                    f.write( content )
                    f.close()
                    self._extract_list.append(arcname)
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
                    aname = relpath(fpath,self._root)

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
        self._extract_list=[]
        for m in self._tar.getmembers():
            if not self._extract_hook_handler( m ):
                self._tar.extract(m.name,self._root)
                self._extract_list.append(m.name)
        return self._extract_list



    def addhook(self,regex ,hook):
        self._hooks.append((re.compile(regex),hook))




class Component(object):


    def __init__( self, config ,name):
        self.config  = config        
        self.name = name
        self.bs = BuildSystem(config)
        self.cookbook = self.bs.cookbook()
        self.recipe = self.cookbook.get_recipe(name)
        self.desc = Description()

        self.desc.name = self.name
        self.desc.platform = self.config.platform
        self.desc.arch = self.config.arch
        self.desc.version = self.recipe.version
    
        self.desc.dependencies=self._deps()


    def _deps(self):
        deps={}
        runtimes = self.cookbook._runtime_deps()
        rdeps = self.cookbook.list_recipe_deps(self.name)
        for recipe in rdeps:
            if self.name == recipe.name or recipe.name in runtimes:
                continue
            deps[recipe.name]=recipe.version
        return deps

    def _mkruntime(self,prefix,output_dir):

        items=[]
        for i in self.recipe.dist_files_list():
            path = os.path.join(self.config.prefix,i )
            if os.path.exists(path):
                items.append(i)

        self.desc.prefix = prefix
        self.desc.type = 'runtime'

        Pack(self.config.prefix,output_dir,self.desc ,items)
        
    def _mkdevel(self,prefix,output_dir):

        items=[]
        for i in self.recipe.devel_files_list():
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


def Pack(prefix,output_dir, desc, items=['']):

    path = os.path.join(output_dir,desc.filename())

    pkg = PkgFile(prefix)
    pkg.open(path,'w')    
    

    pkg.addhook( r'.*\.pc$',pc.Normalizer( prefix ))
    pkg.addhook( r'.*\.la$',la.Normalizer( prefix ))

    pkg.addfile( desc.dump(),".desc")


    for i in items:
        pkg.add(i)    

    pkg.close()