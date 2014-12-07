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

""" Routines that do type checking or create classes
"""
import logging, sys, types
import numpy as np

logger = logging.getLogger(__name__)
    
    
def python_major_version():
    """ Returns 2 or 3 for Python 2.x or 3.x respectively
    """
    return sys.version_info[0]

def python2():
    """ Returns True if we are running python 2
    """
    major_version = sys.version_info[0]
    assert major_version == 2 or major_version == 3, "major_version = {!r}".format(major_version)
    return major_version == 2
    

if python2():
    StringType = basestring
else:
    StringType = str
     

def remove_process_serial_number(arg_list):
    """ Creates a copy of a list (typically sys.argv) where the strings that
        start with '-psn_0_' are removed.
        
        These are the process serial number used by the OS-X open command
        to bring applications to the front. They clash with argparse.
        See: http://hintsforums.macworld.com/showthread.php?t=11978
    """
    return [arg for arg in arg_list if not arg.startswith("-psn_0_")]


def type_name(var):
    """ Returns the name of the type of var"""
    return type(var).__name__
    

def is_a_string(var):
    """ Returns True if var is a string (regular or unicode)

        :param var: variable of which we want to know if it is a string
        :type var: any type
        :returns: True if var is of type string
        :rtype: Boolean
    """
    return isinstance(var, StringType)


def is_a_sequence(var):
    """ Returns True if var is a list or a tuple (but not a string!)
    """
    return (type(var) == list or type(var) == tuple)


def check_is_a_string(var):
    """ Calls is_a_sequence and raises a type error if the check fails.
    """
    if not is_a_string(var):
        raise TypeError("var must be a string, however type(var) is {}"
                        .format(type(var)))
    

def check_is_a_sequence(var):
    """ Calls is_a_sequence and raises a type error if the check fails.
    """
    if not is_a_sequence(var):
        raise TypeError("var must be a list or tuple, however type(var) is {}"
                        .format(type(var)))
    

def is_a_mapping(var):
    """ Returns True if var is a dictionary # TODO: ordered dict 
    """
    return isinstance(var, dict)


def check_is_a_mapping(var):
    """ Calls is_a_mapping and raises a type error if the check fails.
    """
    if not is_a_mapping(var):
        raise TypeError("var must be a dict, however type(var) is {}"
                        .format(type(var)))
    

def is_an_array(var):
    """ Returns True if var is a dictionary # TODO: ordered dict 
    """
    return isinstance(var, np.ndarray)


def check_is_an_array(var):
    """ Calls is_a_mapping and raises a type error if the check fails.
    """
    if not is_an_array(var):
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

def prepend_point_to_extension(extension):
    """ Prepends a point to the extension of it doesn't already start with it
    """
    if extension.startswith('.'):
        return extension
    else:
        return '.' + extension