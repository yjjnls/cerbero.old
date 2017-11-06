
import platform
import os
import shutil
import tempfile
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
    from cerbero.build.filesprovider import FilesProvider
    from cerbero.config import Platform

    FilesProvider.EXTENSIONS[Platform.WINDOWS]['sregex']= \
    FilesProvider._DLL_REGEX = \
    r'^(lib)?{}(-[0-9]+)?([\-_][0-9]+)?(-x64)?\.dll$' # arch suffix
    
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


#bootstrap windows

_old_install_python_sdk=cerbero.bootstrap.windows.WindowsBootstrapper.install_python_sdk

def _install_python_sdk(self):
    try:
        from cerbero.utils import shell
        from cerbero.utils import messages as m

        url='https://github.com/Mingyiz/cerbero/releases/download/v0.1/python27-windows.tar.bz2'
        m.action(_("Installing Python headers"))
        tmp_dir = tempfile.mkdtemp()

        filename=os.path.basename(url)

        path =os.path.join(tmp_dir,filename)

        shell.download(url,path)
    
        python_headers = os.path.join(self.prefix, 'include', 'Python2.7')
        python_headers = to_unixpath(os.path.abspath(python_headers))

        shell.call('mkdir -p %s' % python_headers)
        python_libs = os.path.join(self.prefix, 'lib')
        python_libs = to_unixpath(python_libs)

        temp = to_unixpath(os.path.abspath(tmp_dir))
        shell.call('cp -f %s/windows-external-sdk/python27/%s/include/* %s' %
                    (temp, self.version, python_headers))
        shell.call('cp -f %s/windows-external-sdk/python27/%s/lib/* %s' %
                    (temp, self.version, python_libs))
        try:
            os.remove('%s/lib/python.dll' % self.prefix)
        except:
            pass
        shell.call('ln -s python27.dll python.dll', '%s/lib' % self.prefix)
        shutil.rmtree(tmp_dir)
    except:        
        _old_install_python_sdk

cerbero.bootstrap.windows.WindowsBootstrapper.install_python_sdk=_install_python_sdk