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
import numbers

import numpy as np
import numpy.ma as ma

from argos.external import six

logger = logging.getLogger(__name__)

# For al list of encodings the the standard library see.
if six.PY2:
    URL_PYTHON_ENCODINGS_DOC = "https://docs.python.org/2/library/codecs.html#standard-encodings"
else:
    URL_PYTHON_ENCODINGS_DOC = "https://docs.python.org/3/library/codecs.html#standard-encodings"


#pylint: enable=C0103



###################
# Type conversion #
###################


# def masked_to_regular_array(masked_array, replacement_value=np.nan):
#     """ Returns a copy of the masked array where masked values have been replaced with fill values.
#
#         If masked_array is a regular numpy.ndarry, the function works, meaning a copy of the array
#         is returned.
#
#         :param masked_array: numpy masked
#         :param replacement_value: replacement value (default=np.nan).
#             If None the masked_array.fill_value is used.
#         :return: numpy.ndarray with masked arrays replaced by the fill_vluae
#     """
#     return ma.filled(masked_array, fill_value=replacement_value)

#
# def replace_missing_values(array, missing_value, replacement_value):
#     """ Returns a copy of the array where the missing_values are replaced with replacement_value.
#
#         If missing_value is None, nothing is replaced, a copy of the array is returned..
#         The missing_value can be Nan or infinite, these are replaced.
#
#         If array is a masked array the masked value are replaced (masked_to_regular_array).
#     """
#     if isinstance(array, ma.MaskedArray):
#         logger.debug("^^^^^^^^^^^^^^^^^^^ mask: {}".format(array.mask))
#
#         return array
#         return masked_to_regular_array(array, replacement_value=replacement_value)
#     if missing_value is None:
#         array = np.copy(array)
#     elif np.isnan(missing_value):
#         array[np.isnan(array)] = replacement_value
#     else:
#         array[array == missing_value] = replacement_value
#
#     return array

def environment_var_to_bool(env_var):
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
    elif is_a_string(env_var):
        env_var = env_var.lower().strip()
        if env_var in "false":
            return False
        else:
            return True
    else:
        return bool(env_var)


def fill_values_to_nan(masked_array):
    """ Replaces the fill_values of the masked array by NaNs

        If the array is None or it does not contain floating point values, it cannot contain NaNs.
        In that case the original array is returned.
    """
    if masked_array is not None and masked_array.dtype.kind == 'f':
        check_class(masked_array, ma.masked_array)
        logger.debug("Replacing fill_values by NaNs")
        masked_array[:] = ma.filled(masked_array, np.nan)
        masked_array.set_fill_value(np.nan)
    else:
        return masked_array


# Needed because boolean QSettings in Pyside are converted incorrect the second
# time in Windows (and Linux?) because of a bug in Qt. See:
# https://www.mail-archive.com/pyside@lists.pyside.org/msg00230.html
def setting_str_to_bool(s):
    """ Converts 'true' to True and 'false' to False if s is a string
    """
    if isinstance(s, six.string_types):
        s = s.lower()
        if s == 'true':
            return True
        elif s == 'false':
            return False
        else:
            return ValueError('Invalid boolean representation: {!r}'.format(s))
    else:
        return s


#################
# Type checking #
#################

# Use '{!r}' as default float format for Python 2. This will convert the floats with repr(), which
# is necessary because str() or an empty format string will only print 2 decimals behind the point.
# In Python 3 this is not necessary: all relevant decimals are printed.
DEFAULT_NUM_FORMAT = '{!r}' if six.PY2 else '{}'

def to_string(var, masked=None, decode_bytes='utf-8', maskFormat='', strFormat='{}',
              intFormat='{}', numFormat=DEFAULT_NUM_FORMAT, noneFormat='{!r}', otherFormat='{}'):
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
    if is_binary(var):
        fmt = strFormat
        try:
            decodedVar = var.decode(decode_bytes, 'replace')
        except LookupError as ex:
            # Add URL to exception message.
            raise LookupError("{}\n\nFor a list of encodings in Python see: {}"
                              .format(ex, URL_PYTHON_ENCODINGS_DOC))
    elif is_text(var):
        fmt = strFormat
        decodedVar = six.text_type(var)
    elif is_a_string(var):
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
        except TypeError as ex:
            allMasked = bool(masked)

        if allMasked:
            fmt = maskFormat

    try:
        result = fmt.format(decodedVar)
    except Exception:
        result = "Invalid format {!r} for: {!r}".format(fmt, decodedVar)

    #if masked:
    #    logger.debug("to_string (fmt={}): {!r} ({}) -> result = {!r}".format(maskFormat, var, type(var), result))

    return result


def is_a_string(var, allow_none=False):
    """ Returns True if var is a string (ascii or unicode)

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   True  False
         'string literal'  True  True
        u'unicode literal' True  True

        Also returns True if the var is a numpy string (numpy.string_, numpy.unicode_).
    """
    return isinstance(var, six.string_types) or (var is None and allow_none)


def check_is_a_string(var, allow_none=False):
    """ Calls is_a_string and raises a type error if the check fails.
    """
    if not is_a_string(var, allow_none=allow_none):
        raise TypeError("var must be a string, however type(var) is {}"
                        .format(type(var)))


def is_text(var, allow_none=False):
    """ Returns True if var is a unicode text

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   False False
         'string literal'  False True
        u'unicode literal' True  True

        Also works with the corresponding numpy types.
    """
    return isinstance(var, six.text_type) or (var is None and allow_none)

# Not used yet
# def check_is_text(var, allow_none=False):
#     """ Calls is_text and raises a type error if the check fails.
#     """
#     if not is_text(var, allow_none=allow_none):
#         raise TypeError("var must be a text (unicode str), however type(var) is {}"
#                         .format(type(var)))


def is_binary(var, allow_none=False):
    """ Returns True if var is a binary (bytes) objects

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   True  True
         'string literal'  True  False
        u'unicode literal' False False

        Also works with the corresponding numpy types.
    """
    return isinstance(var, six.binary_type) or (var is None and allow_none)


# Not used yet
# def check_is_text(var, allow_none=False):
#     """ Calls is_binary and raises a type error if the check fails.
#     """
#     if not is_binary(var, allow_none=allow_none):
#         raise TypeError("var must be a binary (bytes), however type(var) is {}"
#                         .format(type(var)))


# Not used. Remove?
# def is_a_numpy_string(var, allow_none=False):
#     """ Returns True if var is of type: numpy.string_, numpy.unicode_
#
#         :param var: variable of which we want to know if it is a string
#         :type var: any type
#         :returns: True if var is of type string
#         :rtype: Boolean
#     """
#     return isinstance(var, (np.string_, np.unicode_)) or (var is None and allow_none)


def is_a_sequence(var, allow_none=False):
    """ Returns True if var is a list or a tuple (but not a string!)
    """
    return isinstance(var, (list, tuple)) or (var is None and allow_none)


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
    """ Returns True if var is a numpy array.
    """
    return isinstance(var, np.ndarray) or (var is None and allow_none)


def check_is_an_array(var, allow_none=False):
    """ Calls is_an_array and raises a type error if the check fails.
    """
    if not is_an_array(var, allow_none=allow_none):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))


def array_is_structured(array):
    """ Returns True if the array has a structured data type.
    """
    return bool(array.dtype.names)


def array_has_real_numbers(array):
    """ Uses the dtype kind of the numpy array to determine if it represents real numbers.

        That is, the array kind should be one of: i u f

        Possible dtype.kind values.
            b 	boolean
            i 	signed integer
            u 	unsigned integer
            f 	floating-point
            c 	complex floating-point
            m 	timedelta
            M 	datetime
            O 	object
            S 	(byte-)string
            U 	Unicode
            V 	void
    """
    kind = array.dtype.kind
    assert kind in 'biufcmMOSUV', "Unexpected array kind: {}".format(kind)
    return kind in 'iuf'


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


#############
# Type info #
#############

# TODO: get_class_name and type_name the same? Not for old style classes
# #http://stackoverflow.com/questions/1060499/difference-between-typeobj-and-obj-class

def type_name(var):
    """ Returns the name of the type of var"""
    return type(var).__name__


def get_class_name(obj):
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

def import_symbol(full_symbol_name):
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
