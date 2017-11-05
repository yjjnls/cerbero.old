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
import hashlib
from cerbero.utils import shell, to_unixpath

def SHA1(fineName, block_size=64 * 1024):
  with open(fineName, 'rb') as f:
    sha1 = hashlib.sha1()
    while True:
      data = f.read(block_size)
      if not data:
        break
      sha1.update(data)
    digest = sha1.hexdigest()
    return digest




def path_join(prefix,*items):
    for i in items:
        i= i.strip('/')
        if i and not i=='.':
            prefix +='/'+i
    return prefix

def relpath(path, prefix):
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
