# -*- coding: utf-8 -*-
# This file is part of Argos.
# 
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

""" Defines a global Inspector registry to register plugins.
"""

import logging, inspect
from libargos.utils.cls import import_symbol, check_is_a_string

logger = logging.getLogger(__name__)



class RegisteredInspector(object):
    """ Class to keep track of a registered Inspector.
        Has a create() method that functions as an Inspector factory.
    """
    def __init__(self, fullName, inspectorClass, library):
        self.fullName = fullName
        self.inspectorClass = inspectorClass
        self.library = library
        # TODO: register shortcuts?
                
    def __repr__(self):
        return "<RegisteredInspector: {}>".format(self.shortName)
        
    @property
    def shortName(self):
        """ Short name for use in file dialogs, menus, etc.
        """
        return self.inspectorClass.classLabel()
        
    @property
    def descriptionHtml(self):
        """ Short name for use in file dialogs, menus, etc.
        """
        return self.inspectorClass.descriptionHtml()


    @property
    def docString(self):
        """ A cleaned up version of the doc string. 
            Can serve as backup in case descriptionHtml is empty.
        """
        return inspect.cleandoc(self.inspectorClass.__doc__)    
        
    @property
    def axesNames(self):
        """ The axes names of the inspector.
        """
        return self.inspectorClass.axesNames()

    @property
    def nDims(self):
        """ The number of axes of this inspector
        """
        return len(self.axesNames)
    
    def create(self, collector):
        """ Creates an inspector of the registered and passes the collector to the constructor.
        """
        return self.inspectorClass(collector)



class InspectorRegistry(object):
    """ Class that can be used to register Inspectors.
        Maintains a name to InspectorClass mapping. 
    """
    def __init__(self):
        """ Constructor
        """
        self._registeredInspectors = []
    
    
    @property
    def registeredInspectors(self):
        return self._registeredInspectors

            
    def registerInspector(self, fullName, library=''):
        """ Register which Inspector when a particular short cut is used.
                
            :param fullName: full name of the inspector. 
                E.g.: 'libargos.plugins.inspector.ncdf.NcdfFileInspector'
                The inspector should be a descendant of BaseInspector
            :param library
        """
        logger.info("Registering {}".format(fullName))
        
        check_is_a_string(fullName)
        inspectorClass = import_symbol(fullName) # TODO: check class? 
        
        regInspector = RegisteredInspector(fullName, inspectorClass, library=library)
        self._registeredInspectors.append(regInspector)
    
