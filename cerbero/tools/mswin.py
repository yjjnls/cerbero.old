
import errno
import os
import sys




def _RegistryGetValue(key, value):
  """Use the _winreg module to obtain the value of a registry key.

  Args:
    key: The registry key.
    value: The particular registry value to read.
  Return:
    contents of the registry key's value, or None on failure.  Throws
    ImportError if _winreg is unavailable.
  """
  import _winreg
  try:
    root, subkey = key.split('\\', 1)
    assert root == 'HKLM'  # Only need HKLM for now.
    with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, subkey) as hkey:
      return _winreg.QueryValueEx(hkey, value)[0]
  except WindowsError:
    return None


class ActivePerl(object):
    def __init__(self,path,version):
        self.path = path
        self.version = version

    def Path(self):
        return self.path

    def Version(self):
        return self.version

def _ActivePerl(name,version):
    for key in [r'HKLM\Software\ActiveState\ActivePerl',
            r'HKLM\Software\Wow6432Node\ActiveState\ActivePerl']:
        version = _RegistryGetValue(key,'CurrentVersion')
        if version:
            path = _RegistryGetValue('%s\\%s'%(key,version),None)
            if path:
                return ActivePerl(path,version)
    return None

def find(name,version=None):
    """find software operation object.

    Args:
        name: name of software. 'MSVS',ActivePerl
        version: version of the tool, None mean auto selecte
    Return:
        object of software, or None on failure.
    """
    name = name.lower()
    if name == 'activeperl':
        return _ActivePerl(name,version)
    elif name == 'msvs':
        import MSVSVersion
        return MSVSVersion.SelectVisualStudioVersion(version)
    return None

    
def vcvars(version,arch):
    """ return Visual Studio native tools vars init command 
    """
    from cerbero.config import Architecture

    msvs = find('MSVS',version)
    archmap={
        Architecture.X86 : 'x86',
        Architecture.X86_64 : 'x64'
    }
    script = msvs.SetupScript(archmap[arch])
    return '"%s" %s'%(script[0],script[1])

def perl(name='ActivePerl'):
    perl = find('ActivePerl')
    assert perl        
    return  perl.path +r'bin\perl.exe'

if __name__ == '__main__':
    msvs = find('MSVS',2015)
    print msvs.Path()
    print msvs.SetupScript('x86')
    x= msvs.DefaultToolset()
    print x
    perl = find('ActivePerl')
    print perl.Path()
    print perl.Version()


