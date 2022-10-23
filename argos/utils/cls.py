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

    The module name is short for 'Class'
"""
from __future__ import annotations

from typing import Any, Dict, Type, Optional

import logging
import numbers
import re

import numpy as np
import numpy.ma as ma

logger = logging.getLogger(__name__)

# For al list of encodings the standard library see.
URL_PYTHON_ENCODINGS_DOC = "https://docs.python.org/3/library/codecs.html#standard-encodings"



###################
# Type conversion #
###################
#
# def environmentVarToBool(envVar: str) -> bool:
#     """ Converts an environment variable to a boolean
#
#         Returns False if the environment variable is False, 0 or a case-insensitive string "false"
#         or "0".
#     """
#
#     # Try to see if envVar can be converted to an int
#     try:
#         envVar = int(envVar)
#     except ValueError:
#         pass
#
#     if isinstance(envVar, numbers.Number):
#         return bool(envVar)
#     elif isAString(envVar):
#         envVar = envVar.lower().strip()
#         if envVar in "false":
#             return False
#         else:
#             return True
#     else:
#         return bool(envVar)


def fillValuesToNan(maskedArray: Optional[ma.masked_array]) -> Optional[ma.masked_array]:
    """ Replaces the fill_values of the masked array by NaNs

        If the array is None, or it does not contain floating point values, it cannot contain NaNs.
        In that case the original array is returned.
    """
    if maskedArray is not None and maskedArray.dtype.kind == 'f':
        checkType(maskedArray, ma.masked_array)
        logger.debug("Replacing fill_values by NaNs")
        maskedArray[:] = ma.filled(maskedArray, np.nan)
        maskedArray.set_fill_value(np.nan)
        return maskedArray
    else:
        return maskedArray


#################
# Type checking #
#################

_DEFAULT_NUM_FORMAT = '{}'  # Will print all relevant decimals (in Python 3)

def toString(var: Any, *,
             masked: Any = None,
             decodeBytesAs: str = 'utf-8',
             maskFormat: str = '',
             strFormat: str = '{}',
             intFormat: str = '{}',
             numFormat: str = _DEFAULT_NUM_FORMAT,
             noneFormat: str = '{!r}',
             otherFormat: str = '{}') -> str:
    """ Converts variable to a python using the appropriate format string.

        For the possible format string (replacement fields) see
            https://docs.python.org/3/library/string.html#format-string-syntax

        If var consists of a numpy.str_, the result will be converted to a regular Python string.
        This is necessary to display the string in Qt widgets.

        If var consists of bytes, the decodeBytesAs is used to decode the bytes.

        Args:
            var: The variable to be checked.
            masked: If True, the element is masked so the maskFormat will be used.
                In case it is a sequence, all elements must be true for the maskFormate to be used.
            decodeBytesAs: String containing the expected encoding when var is of type bytes
            strFormat: New style format string used to format strings
            intFormat: New style format string used to format integers
            numFormat: New style format string used to format all numbers except integers.
            noneFormat: New style format string used to format Nones.
            maskFormat: This format string is used if masked is True.
                If the maskFormat is empty, the format is never overridden.
            otherFormat: New style format string used to format all other types.
    """
    #logger.debug("to_string: {!r} ({})".format(var, type(var)))

    # Decode and select correct format specifier.
    if isBinary(var):
        fmt = strFormat
        try:
            decodedVar = var.decode(decodeBytesAs, 'replace')
        except LookupError as ex:
            # Add URL to exception message.
            raise LookupError("{}\n\nFor a list of encodings in Python see: {}"
                              .format(ex, URL_PYTHON_ENCODINGS_DOC)) from ex
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


def isAString(var: Any, allowNone: bool = False) -> bool:
    """ Returns True if var is a string

        Also returns True if the var is a numpy string.
    """
    return isinstance(var, str) or (var is None and allowNone)


def checkIsAString(var: Any, allowNone: bool = False):
    """ Calls isAString and raises a TypeError if the check fails.
    """
    if not isAString(var, allowNone=allowNone):
        raise TypeError("var must be a string, however type(var) is {}"
                        .format(type(var)))


def isBinary(var: Any, allowNone: bool = False) -> bool:
    """ Returns True if var is a binary (bytes) object.

        Also works with the corresponding numpy types.
    """
    return isinstance(var, bytes) or (var is None and allowNone)


def isASequence(var: Any, allowNone: bool = False) -> bool:
    """ Returns True if var is a list or a tuple (but not a string!)
    """
    return isinstance(var, (list, tuple)) or (var is None and allowNone)


def checkIsASequence(var: Any, allowNone: bool = False):
    """ Calls isASequence and raises a TypeError if the check fails.
    """
    if not isASequence(var, allowNone=allowNone):
        raise TypeError("var must be a list or tuple, however type(var) is {}"
                        .format(type(var)))


def isAMapping(var: Any, allowNone: bool = False) -> bool:
    """ Returns True if var is a dictionary.
    """
    return isinstance(var, dict) or (var is None and allowNone)


def checkIsAMapping(var: Any, allowNone: bool = False):
    """ Calls isAMapping and raises a TypeError if the check fails.
    """
    if not isAMapping(var, allowNone=allowNone):
        raise TypeError("var must be a dict, however type(var) is {}"
                        .format(type(var)))


def isAnArray(var: Any, allowNone: bool = False) -> bool:
    """ Returns True if var is a numpy array.
    """
    return isinstance(var, np.ndarray) or (var is None and allowNone)


def checkIsAnArray(var: Any, allowNone: bool = False):
    """ Calls is_an_array and raises a TypeError if the check fails.
    """
    if not isAnArray(var, allowNone=allowNone):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))


def arrayIsStructured(array: np.ndarray) -> bool:
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


def arrayKindLabel(array: np.ndarray) -> str:
    """ Returns short string describing the array data type kind.
    """
    return KIND_LABEL[array.dtype.kind]


def arrayHasRealNumbers(array: np.ndarray) -> bool:
    """ Uses the dtype.kind of the numpy array to determine if it represents real numbers.

        That is, the array kind should be one of: i u f.
    """
    kind = array.dtype.kind
    return kind in 'iuf'


def checkType(var: Any, targetClass: Type, allowNone: bool = False):
    """ Checks that a varaible is a (sub)type of target_class.

        Raises a TypeError if this is not the case, does nothing if it is.

        Args:
            var: The variable whose type is to be checked.
            targetClass: The target type/class.
            allowNone: If True, var may be None.
    """
    if not isinstance(var, targetClass):
        if not (allowNone and var is None):
            raise TypeError("obj must be a of type {}, got: {}"
                            .format(targetClass, type(var)))


COLOR_REGEXP = re.compile('^#[0-9A-Fa-f]{6}$')  # Hex color string representation

def isAColorString(colorStr: str, allowNone: bool = False) -> bool:
    """ Returns True if colorStr is a string starting with '#' followed by 6 hexadecimal digits.
    """
    if not isAString(colorStr, allowNone=allowNone):
        return False

    return bool(COLOR_REGEXP.match(colorStr))


def checkIsAColorString(var: Any, allowNone: bool = False):
    """ Calls is_an_array and raises a TypeError if the check fails.
    """
    if not checkIsAColorString(var, allowNone=allowNone):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))


#############
# Type info #
#############


def typeName(var: Any) -> str:
    """ Returns the name of the type of var.
    """
    return type(var).__name__


#############
# Importing #
#############


def importSymbol(fullSymbolName: str) -> Any:
    """ Imports a symbol (e.g. class, variable, etc.) from a dot separated name.

        Can be used to create a class whose type is only known at run-time.

        Args:
            fullSymbolName: Symbol name that includes the packages name(s).
                For instance: `argos.plugins.rti.ncdf.NcdfFileRti`

        Raises:
            ImportError: If the module doesn't exist.
            AttributeError: If the class doesn't exist.

        Returns:
            The imported symbol.

    """
    parts = fullSymbolName.rsplit('.', 1)
    if len(parts) == 2:
        moduleName, symbolName = parts
        moduleName = str(moduleName) # convert from possible unicode
        symbolName = str(symbolName)
        #logger.debug("From module {} importing {!r}".format(module_name, symbol_name))
        module = __import__(moduleName, fromlist=[symbolName])
        cls = getattr(module, symbolName)
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
    def instance(cls, **kwargs) -> SingletonMixin:
        """ Returns the singleton's instance.

            Args:
                kwargs: Keyword arguments are passed to the class constructor.
        """
        if cls in SingletonMixin.__singletons:
            return SingletonMixin.__singletons[cls]
        else:
            return cls(**kwargs)


    @classmethod
    def _checkNotYetPresent(cls) -> None:
        """ Checks that the newClass is not yet present in the singleton.

            Also check that no descendants are present. This is typically due to bugs.
        """
        assert cls not in SingletonMixin.__singletons, "Constructor called twice: {}".format(cls)

        for existingClass in SingletonMixin.__singletons.keys():
            assert not issubclass(cls, existingClass), \
                "Sub type of {} already present: {}".format(cls, existingClass)

            assert not issubclass(existingClass, cls), \
                "Ancestor of {} already present: {}".format(cls, existingClass)


