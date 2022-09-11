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

""" Module that contains functions that have to do with type checking, importing, etc.

    The name is short for 'Class'
"""
from __future__ import annotations

from typing import Any, Dict, Type

import logging
import numbers
import re

import numpy as np
import numpy.ma as ma


logger = logging.getLogger(__name__)

# For al list of encodings the standard library see.
URL_PYTHON_ENCODINGS_DOC = "https://docs.python.org/3/library/codecs.html#standard-encodings"


# Temporary disable invalid names until we have decided on camelCase or snake_case here.
#pylint: disable=invalid-name

###################
# Type conversion #
###################

def environmentVarToBool(env_var):
    """ Converts an environment variable to a boolean

        Returns False if the environment variable is False, 0 or a case-insenstive string "false"
        or "0".
    """

    # Try to see if env_var can be converted to an int
    try:
        env_var = int(env_var)
    except ValueError:
        pass

    if isinstance(env_var, numbers.Number):
        return bool(env_var)
    elif isAString(env_var):
        env_var = env_var.lower().strip()
        if env_var in "false":
            return False
        else:
            return True
    else:
        return bool(env_var)


def fillValuesToNan(masked_array):
    """ Replaces the fill_values of the masked array by NaNs

        If the array is None or it does not contain floating point values, it cannot contain NaNs.
        In that case the original array is returned.
    """
    if masked_array is not None and masked_array.dtype.kind == 'f':
        chechType(masked_array, ma.masked_array)
        logger.debug("Replacing fill_values by NaNs")
        masked_array[:] = ma.filled(masked_array, np.nan)
        masked_array.set_fill_value(np.nan)
    else:
        return masked_array


#################
# Type checking #
#################

_DEFAULT_NUM_FORMAT = '{}'  # Will print all relevant decimals (in Python 3)

def toString(var, masked=None, decode_bytes='utf-8', maskFormat='', strFormat='{}',
             intFormat='{}', numFormat=_DEFAULT_NUM_FORMAT, noneFormat='{!r}', otherFormat='{}'):
    """ Converts var to a python string or unicode string so Qt widgets can display them.

        If var consists of bytes, the decode_bytes is used to decode the bytes.

        If var consists of a numpy.str_, the result will be converted to a regular Python string.
        This is necessary to display the string in Qt widgets.

        For the possible format string (replacement fields) see:
            https://docs.python.org/3/library/string.html#format-string-syntax

        :param masked: if True, the element is masked. The maskFormat is used.
        :param decode_bytes': string containing the expected encoding when var is of type bytes
        :param strFormat' : new style format string used to format strings
        :param intFormat' : new style format string used to format integers
        :param numFormat' : new style format string used to format all numbers except integers.
        :param noneFormat': new style format string used to format Nones.
        :param maskFormat': override with this format used if masked is True.
            If the maskFormat is empty, the format is never overriden.
        :param otherFormat': new style format string used to format all other types
    """
    #logger.debug("to_string: {!r} ({})".format(var, type(var)))

    # Decode and select correct format specifier.
    if isBinary(var):
        fmt = strFormat
        try:
            decodedVar = var.decode(decode_bytes, 'replace')
        except LookupError as ex:
            # Add URL to exception message.
            raise LookupError("{}\n\nFor a list of encodings in Python see: {}"
                              .format(ex, URL_PYTHON_ENCODINGS_DOC)) from ex
    # elif is_text(var):   # is 'str' in Python 3
    #     fmt = strFormat
    #     decodedVar = six.text_type(var)
    elif isAString(var):
        fmt = strFormat
        decodedVar = str(var)
    elif isinstance(var, numbers.Integral):
        fmt = intFormat
        decodedVar = var
    elif isinstance(var, numbers.Number):
        fmt = numFormat
        decodedVar = var
    elif var is None:
        fmt = noneFormat
        decodedVar = var
    else:
        fmt = otherFormat
        decodedVar = var

    if maskFormat != '{}':
        try:
            allMasked = all(masked)
        except TypeError:
            allMasked = bool(masked)

        if allMasked:
            fmt = maskFormat

    try:
        result = fmt.format(decodedVar)
    except Exception:
        result = "Invalid format {!r} for: {!r}".format(fmt, decodedVar)

    # if masked:
    #    logger.debug("to_string (fmt={}): {!r} ({}) -> result = {!r}"
    #                 .format(maskFormat, var, type(var), result))

    return result


def isAString(var, allow_none=False):
    """ Returns True if var is a string (ascii or unicode)

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   True  False
         'string literal'  True  True
        u'unicode literal' True  True

        Also returns True if the var is a numpy string (numpy.string_, numpy.unicode_).
    """
    return isinstance(var, str) or (var is None and allow_none)


def checkIsAString(var, allow_none=False):
    """ Calls is_a_string and raises a type error if the check fails.
    """
    if not isAString(var, allow_none=allow_none):
        raise TypeError("var must be a string, however type(var) is {}"
                        .format(type(var)))


def isBinary(var, allow_none=False):
    """ Returns True if var is a binary (bytes) objects

        Also works with the corresponding numpy types.
    """
    return isinstance(var, bytes) or (var is None and allow_none)


def isASequence(var, allow_none=False):  # TODO: use iterable?
    """ Returns True if var is a list or a tuple (but not a string!)
    """
    return isinstance(var, (list, tuple)) or (var is None and allow_none)


def checkIsASequence(var, allow_none=False):
    """ Calls is_a_sequence and raises a type error if the check fails.
    """
    if not isASequence(var, allow_none=allow_none):
        raise TypeError("var must be a list or tuple, however type(var) is {}"
                        .format(type(var)))


def isAMapping(var, allow_none=False):
    """ Returns True if var is a dictionary
    """
    return isinstance(var, dict) or (var is None and allow_none)


def checkIsAMapping(var, allow_none=False):
    """ Calls is_a_mapping and raises a type error if the check fails.
    """
    if not isAMapping(var, allow_none=allow_none):
        raise TypeError("var must be a dict, however type(var) is {}"
                        .format(type(var)))


def isAnArray(var, allow_none=False):
    """ Returns True if var is a numpy array.
    """
    return isinstance(var, np.ndarray) or (var is None and allow_none)


def checkIsAnArray(var, allow_none=False):
    """ Calls is_an_array and raises a type error if the check fails.
    """
    if not isAnArray(var, allow_none=allow_none):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))


def arrayIsStructured(array):
    """ Returns True if the array has a structured data type.
    """
    return bool(array.dtype.names)


KIND_LABEL = dict(
    b = 'boolean',
    i = 'signed integer',
    u = 'unsigned integer',
    f = 'floating-point',
    c = 'complex floating-point',
    m = 'timedelta',
    M = 'datetime',
    O = 'object',
    S = 'byte/string',
    U = 'unicode',
    V = 'compound', # is more clear to end users than 'void'
)


def arrayKindLabel(array):
    """ Returns short string describing the array data type kind
    """
    return KIND_LABEL[array.dtype.kind]


def arrayHasRealNumbers(array):
    """ Uses the dtype kind of the numpy array to determine if it represents real numbers.

        That is, the array kind should be one of: i u f

        Possible dtype.kind values.

    """
    kind = array.dtype.kind
    return kind in 'iuf'


def chechType(obj, target_class, allow_none = False):
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


COLOR_REGEXP = re.compile('^#[0-9A-Fa-f]{6}$')  # Hex color string representation

def isAColorString(colorStr, allow_none=False):
    """ Returns True if colorStr is a string starting with '#' folowed by 6 hexadecimal digits.
    """
    if not isAString(colorStr, allow_none=allow_none):
        return False

    return COLOR_REGEXP.match(colorStr)



def checkIsAColorString(var, allow_none=False):
    """ Calls is_an_array and raises a type error if the check fails.
    """
    if not checkIsAColorString(var, allow_none=allow_none):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))


#############
# Type info #
#############

# TODO: get_class_name and type_name the same? Not for old style classes.
#  Fix when only using Python 3
# #http://stackoverflow.com/questions/1060499/difference-between-typeobj-and-obj-class

def typeName(var):
    """ Returns the name of the type of var"""
    return type(var).__name__


def getClassName(obj):
    """ Returns the class name of an object.
    """
    return obj.__class__.__name__


def get_full_class_name(obj):
    """ Returns the full class name of an object. This includes packages and module names.

        It depends on where the class is imported so only use for testing and debugging!
    """
    return "{}.{}".format(obj.__class__.__module__, obj.__class__.__name__)

#############
# Importing #
#############

# TODO: use importlib.import_module?
# Perhaps in Python 3. As long as the code below works there is no need to change it.
def importSymbol(full_symbol_name):
    """ Imports a symbol (e.g. class, variable, etc) from a dot separated name.
        Can be used to create a class whose type is only known at run-time.

        The full_symbol_name must contain packages and module,
        e.g.: 'argos.plugins.rti.ncdf.NcdfFileRti'

        If the module doesn't exist an ImportError is raised.
        If the class doesn't exist an AttributeError is raised.
    """
    parts = full_symbol_name.rsplit('.', 1)
    if len(parts) == 2:
        module_name, symbol_name = parts
        module_name = str(module_name) # convert from possible unicode
        symbol_name = str(symbol_name)
        #logger.debug("From module {} importing {!r}".format(module_name, symbol_name))
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
        


class SingletonMixin():
    """ Mixin to ensure the class is a singleton.

        The instance method is thread-safe but the returned object not! You still have to implement
        your own locking for that.
    """
    __singletons: Dict[Type[Any], SingletonMixin] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        cls = type(self)
        logger.debug("Creating singleton: {} (awaiting lock)".format(cls))
        cls._checkNotYetPresent()
        SingletonMixin.__singletons[cls] = self


    @classmethod
    def instance(cls, **kwargs):
        """ Returns the singleton's instance.
        """
        if cls in SingletonMixin.__singletons:
            return SingletonMixin.__singletons[cls]
        else:
            return cls(**kwargs)


    @classmethod
    def _checkNotYetPresent(cls):
        """ Checks that the newClass is not yet present in the singleton

            Also check that no descendants are present. This is typically due to bugs.
        """
        assert cls not in SingletonMixin.__singletons, "Constructor called twice: {}".format(cls)

        for existingClass in SingletonMixin.__singletons.keys():
            assert not issubclass(cls, existingClass), \
                "Sub type of {} already present: {}".format(cls, existingClass)

            assert not issubclass(existingClass, cls), \
                "Ancestor of {} already present: {}".format(cls, existingClass)


