# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2012 Andoni Morales Alastruey <ylatuya@gmail.com>
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

from collections import defaultdict
import os
import pickle
import time
import imp

import cerbero.build
CookBookBase = cerbero.build.cookbook.CookBook


from cerbero.config import CONFIG_DIR, Platform, Architecture, Distro,\
    DistroVersion, License
from cerbero.build.build import BuildType
from cerbero.build.source import SourceType
from cerbero.errors import FatalError, RecipeNotFoundError, InvalidRecipeError,PackageNotFoundError
from cerbero.utils import _, shell, parse_file
from cerbero.utils import messages as m
from cerbero.build import recipe as crecipe
from cerbero.build.cookbook import RecipeStatus 

class CookBook (CookBookBase):
    '''
    Stores a list of recipes and their build status saving it's state to a
    cache file

    @ivar recipes: dictionary with L{cerbero.recipe.Recipe} availables
    @type recipes: dict
    @ivar status: dictionary with the L{cerbero.cookbook.RecipeStatus}
    @type status: dict
    '''

    RECIPE_EXT = '.recipe'

    def __init__(self, config, load=True):
        CookBookBase.__init__(self,config,load)

    

    def get_recipe(self, name):
        '''
        Gets a recipe from its name

        @param name: name of the recipe
        @type name: str
        '''
        try :
            CookBookBase.get_recipe(self,name)
            desc = self._get_componet_desc(name)
            if desc and not self.status.has_key(name):
                self.status[name] = RecipeStatus(None, 
                steps=[crecipe.BuildSteps.INSTALL,crecipe.BuildSteps.POST_INSTALL],
                needs_build=False,
                built_version = desc['version'])

        except RecipeNotFoundError, e:
            print name ,'-->','NotFound'
            self._load_recipe_from_install(name)


        return self.recipes[name]

    def _load_recipe_from_install(self,name):
        config = self.get_config()
        desc = self._get_componet_desc(name)
        if desc is None:
            raise PackageNotFoundError(name +'(componet install)')
        recipe = crecipe.Recipe(config)
        recipe.name = desc['name']
        recipe.version = desc['version']
        
        for name,version in desc['dependencies'].viewitems():
            recipe.deps.append(name)

        self.add_recipe( recipe )
        self.status[name] = RecipeStatus(None, 
        steps=[crecipe.BuildSteps.INSTALL,crecipe.BuildSteps.POST_INSTALL],
        needs_build=False,
        built_version = recipe.version)

    def _get_componet_desc(self,name):
        descs={}
        config = self.get_config()
        for ctype in ['runtime','devel']:
            instd = os.path.join(config.prefix,'.inst',ctype,name)
            if not os.path.exists(instd):                
                return None
            path = os.path.join(instd,'.desc')
            import yaml
            descs[ctype] = yaml.load( open(path,'r'))
        desc = descs['devel']
        return desc
        



cerbero.build.cookbook.CookBook = CookBook