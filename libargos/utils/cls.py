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

""" 'Class' module that contains functions that have to do with type checking, importing, etc.
    
"""

import logging
import numpy as np

from .misc import python2

logger = logging.getLogger(__name__)
    

if python2():
    StringType = basestring
else:
    StringType = str
         

def type_name(var):
    """ Returns the name of the type of var"""
    return type(var).__name__
    

def is_a_string(var, allow_none=False):
    """ Returns True if var is a string (regular or unicode)

        :param var: variable of which we want to know if it is a string
        :type var: any type
        :returns: True if var is of type string
        :rtype: Boolean
    """
    return isinstance(var, StringType) or (var is None and allow_none)


def is_a_sequence(var, allow_none=False):
    """ Returns True if var is a list or a tuple (but not a string!)
    """
    return (type(var) == list or type(var) == tuple or (var is None and allow_none))


def check_is_a_string(var, allow_none=False):
    """ Calls is_a_sequence and raises a type error if the check fails.
    """
    if not is_a_string(var, allow_none=allow_none):
        raise TypeError("var must be a string, however type(var) is {}"
                        .format(type(var)))
    

def check_is_a_sequence(var, allow_none=False):
    """ Calls is_a_sequence and raises a type error if the check fails.
    """
    if not is_a_sequence(var, allow_none=allow_none):
        raise TypeError("var must be a list or tuple, however type(var) is {}"
                        .format(type(var)))
    

def is_a_mapping(var, allow_none=False):
    """ Returns True if var is a dictionary # TODO: ordered dict 
    """
    return isinstance(var, dict) or (var is None and allow_none)


def check_is_a_mapping(var, allow_none=False):
    """ Calls is_a_mapping and raises a type error if the check fails.
    """
    if not is_a_mapping(var, allow_none=allow_none):
        raise TypeError("var must be a dict, however type(var) is {}"
                        .format(type(var)))
    

def is_an_array(var, allow_none=False):
    """ Returns True if var is a dictionary # TODO: ordered dict 
    """
    return isinstance(var, np.ndarray) or (var is None and allow_none)


def check_is_an_array(var, allow_none=False):
    """ Calls is_a_mapping and raises a type error if the check fails.
    """
    if not is_an_array(var, allow_none=allow_none):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))
    

def check_class(obj, target_class, allow_none = False):
    """ Checks that the  obj is a (sub)type of target_class. 
        Raises a TypeError if this is not the case.

        :param obj: object whos type is to be checked
        :type obj: any type
        :param target_class: target type/class
        :type target_class: any class or type
        :param allow_none: if true obj may be None
        :type allow_none: boolean
    """
    if not isinstance(obj, target_class):
        if not (allow_none and obj is None):
            raise TypeError("obj must be a of type {}, got: {}"
                            .format(target_class, type(obj)))
    

def get_class_name(obj):
    """ Returns the class name of an object.
    """
    return obj.__class__.__name__


def import_symbol(full_symbol_name):
    """ Imports a symbol (e.g. class, variable, etc) from a dot separated name.
        Can be used to create a class whose type is only known at run-time. 
        
        The full_symbol_name must contain packages and module, 
        e.g.: 'libargos.plugins.rti.ncdf.NcdfFileRti'
                
        If the module doesn't exist an ImportError is raised.
        If the class doesn't exist an AttributeError is raised.
    """
    parts = full_symbol_name.rsplit('.', 1)
    if len(parts) == 2:
        module_name, symbol_name = parts
        module_name = str(module_name) # convert from possible unicode
        symbol_name = str(symbol_name)
        logger.debug("From module {} importing {!r}".format(module_name, symbol_name))
        module = __import__(module_name, fromlist=[symbol_name])
        cls = getattr(module, symbol_name)
        return cls
    elif len(parts) == 1:  
        # No module part, only a class name. If you want to create a class
        # by using name without module, you should use globals()[symbol_name]
        # We cannot do this here because globals is of the module that defines
        # this function, not of the modules where this function is called. 
        raise ImportError("full_symbol_name should contain a module")
    else:
        assert False, "Bug: parts should have 1 or elements: {}".format(parts)

