
import platform
import os
import shutil
import cerbero

from cerbero.utils import shell, _, fix_winpath, to_unixpath, git
from cerbero.utils import messages as m

#load auto config
cac={'cerbero':cerbero}
CERBERO_AUTO_CONFIG=None

if not os.path.exists('cerbero.cac'):
    CERBERO_AUTO_CONFIG=os.getenv('CERBERO_AUTO_CONFIG',None)
    if CERBERO_AUTO_CONFIG is not None:
        if os.path.exists( CERBERO_AUTO_CONFIG):
            shutil.copy(CERBERO_AUTO_CONFIG,'cerbero.cac')
        else:            
            shell.download(CERBERO_AUTO_CONFIG,'cerbero.cac')

if os.path.exists('cerbero.cac'):
    import cerbero
    path = os.path.abspath('cerbero.cac')
    print 'Loading',path


    execfile(path,cac)



if platform.system() == 'Windows':
    #import cerbero.bootstrap.build_tools
    #import cerbero.bootstrap.hijack.build_tools
    #cerbero.bootstrap.build_tools.BuildTools = \
    #cerbero.bootstrap.hijack.build_tools.BuildTools

    #overwrite windows bootstrap with hijack one
    import cerbero.bootstrap.bootstrapper
    import cerbero.bootstrap.hijack.windows
    cerbero.bootstrap.hijack.windows.register_all()

    import cerbero.build.build
    import cerbero.build.hijack.cmake
    cerbero.build.build.BuildType.AUTOCMAKE= \
    cerbero.build.hijack.cmake.AutoCMake

import cerbero.commands
_old_load_commands = cerbero.commands.load_commands

def _load_commands(subparsers):
    _old_load_commands(subparsers)

    
    import os
    commands_dir = os.path.abspath(os.path.dirname(__file__)+'/cpm/commands')

    for name in os.listdir(commands_dir):
        name, extension = os.path.splitext(name)
        if extension != '.py':
            continue
        try:
            __import__('cerbero.cpm.commands.%s' % name)
        except ImportError, e:
            m.warning("Error importing command %s:\n %s" % (name, e))
    for command in cerbero.commands._commands.values():
        command.add_parser(subparsers)

cerbero.commands.load_commands = _load_commands


_old_shell_download = shell.download

if cac.get('mirror',None):

    def _hijack_download(url, destination=None, recursive=False, check_cert=True, overwrite=False):
        check_cert = False
        mirror_url = cac['mirror'](url)
        if mirror_url:
            m.message('%s has been redirect to %s.'%(url,mirror_url))
            _old_shell_download( mirror_url,destination,recursive,check_cert,overwrite)
        else:
            _old_shell_download( url,destination,recursive,check_cert,overwrite)
    shell.download = _hijack_download


#
# Installed one will not build
#
#    def get_recipe(self, name):
#        '''
#        Gets a recipe from its name
#
#        @param name: name of the recipe
#        @type name: str
#        '''
#        if name in self._invalid_recipes:
#            raise self._invalid_recipes[name]
#        if name not in self.recipes:
#            raise RecipeNotFoundError(name)
#        return self.recipes[name]
#
import cerbero.build.hijack.cookbook
#_old_CookBook_get_recipe = cerbero.build.cookbook.CookBook.get_recipe
#
#def _CookBook_get_recipe(self,name):
#    from cerbero.errors import RecipeNotFoundError
#
#    try :
#        return _old_CookBook_get_recipe(self,name)
#    except RecipeNotFoundError, e:
#        print '-----------%s----------'% type(e)
#        print e
#        print '--------RecipeNotFoundError-------------'
#        
#    except Exception,e:
#        print '-----------%s----------'% type(e)
#        print e
#        print '---------------------'
#cerbero.build.cookbook.CookBook.get_recipe =_CookBook_get_recipe