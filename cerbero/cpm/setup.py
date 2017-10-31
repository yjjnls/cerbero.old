

import os
import yaml

from cerbero.cpm.utils import SHA1
from cerbero.utils import shell
from cerbero.cpm.packager import PkgFile
from cerbero.cpm import pc,la, PkgFileSkipper

from cerbero.utils import messages as m

class Base(object):
    prefix =None
    cache_dir=None

    def __init__(self,prefix):
        self.prefix = prefix
        self.cache_dir = os.path.join(prefix,'.inst/cache')

    def install(self, repo, filter={}):
        pass

    def uninstall(self, filter={}):
        pass

    def set_cache_dir(self,directory):
        self.cache_dir = os.path.abspath(directory)

    def path( self,url ,sha1=None):
        if os.path.exists(url):
            return url

        basename = os.path.basename(url)
        if not os.path.exists(self.cache_dir):                
            os.makedirs(self.cache_dir)

        path = os.path.join(self.cache_dir,basename)
        if os.path.exists(path):
            if sha1 is None:
                return path
            
            val = SHA1( path)
            if val == sha1:
                return path
            os.remove(path)
        shell.download( url, path)
        if sha1:
            val = SHA1(path)
            assert val == sh1,'''
            error sha-1 check for %s
            expect : %s
            real : %s
            '''%(url,sh1,val)
        return path

    





class Component(Base):

    def __init__(self,prefix):
        Base.__init__(self,prefix)

    def install(self, repo, filter={}):
        pkg = PkgFile(self.prefix,'r')
        
        pkg.addhook( r'.*\.pc$',pc.Extractor(self.prefix))
        pkg.addhook( r'.*\.la$',la.Extractor(self.prefix))
        pkg.addhook( r'.desc$',PkgFileSkipper(self.prefix))

        for filename , info in filter.viewitems():
            sha1=info.get('SHA1',None)
            url = os.path.join(repo,filename)
            path = self.path(url,sha1)

            pkg.open(path,'r')
            content = pkg.read('.desc')
            desc = yaml.load( content )
            name = desc['name']
            version = desc['version']
            ptype = desc['type']
            instd = os.path.join(self.prefix,'.inst',ptype,'%s'%name)
            if os.path.exists(instd):
                m.warning('%s %s already installed, we will overwrite it.'%(name,version))
                
                #FIXME uninstall not do

                #self.uninstall({name:{'version':version}})
            else:
                os.makedirs(instd)
            m.message('install component %s %s (%s)'%(name,version,ptype))
            f=open(os.path.join(instd,'.desc'),'w')
            f.write(content)
            f.close()
            flist  = pkg.extract()
            f =open(os.path.join(instd,'.files'),'w')
            f.write("\n".join(flist))
            f.close()
            pkg.close()

            


    def uninstall(self,filter={}):
        for name , info in filter.viewitems():
            
            version = info.get('version',None)
            for ptype in info.get('type',['runtime']):
                if not version:
                    fpath = os.path.join(self.prefix,'.inst',ptype,'*{0}*'.format(name))
                    found = glob.glob(fpath)
                    print found
                    return

                instd = os.path.join(self.prefix,'.inst',ptype,'%s-%s'%(name,version))

                if not os.path.exists(instd):
                    m.warning('%s %s seems not installed.')
                    return
                f=open(os.path.join(instd,'.files'),'r')
                for filename in f.readlines():
                    path = os.path.join(self.prefix,filename.strip())
                    if os.path.isdir(path):
                        os.removedirs(path)
                    elif os.path.isfile(path):
                        os.remove(path)
                    else:
                        m.warning('%s not exits!'%path)
                f.close()
                import shutil
                #shutil.rmtree(instd)
                os.removedirs(instd)
                #print 'rm -rd %s'%instd
                #shell.call('rm -rd %s'%instd)
                #print '%s removed !'%instd



class Build(Base):

    def __init__(self,prefix):
        Base.__init__(self,prefix)

    def install(self, repo, filter={}):
        
        dbpath = self.path( os.path.join(repo,'Build.yaml') )
        db = yaml.load( open(dbpath,'r'))

        cinstall = Component(self.prefix)

        for name ,com in db.get('component',{}).viewitems():
            version = com['version']
            for ctype in ['runtime','devel']:
                info = com.get(ctype,None)
                if info is None:
                    continue
                
                sha1 = info.get('SHA1',None)
                filename = info['filename']
                cinstall.install( repo, filter={
                    filename:{
                        'type':ctype,
                        'version':version,
                        'SHA1':sha1
                    }
                })



