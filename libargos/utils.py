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
