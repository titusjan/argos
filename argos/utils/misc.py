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

""" Miscellaneous routines.
"""
import logging, sys
import pprint

from html import escape

from argos.external.six import unichr
from argos.utils.cls import is_a_string

logger = logging.getLogger(__name__)

class NotSpecified(object):
    """ Class for NOT_SPECIFIED constant.
        Is used so that a parameter can have a default value other than None.

        Evaluate to False when converted to boolean.
    """
    def __nonzero__(self):
        """ Always returns False. Called when to converting to bool in Python 2.
        """
        return False

    def __bool__(self):
        """ Always returns False. Called when to converting to bool in Python 3.
        """
        return False



NOT_SPECIFIED = NotSpecified()



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


def is_quoted(s):
    """ Returns True if the string begins and ends with quotes (single or double)

        :param s: a string
        :return: boolean
    """
    return (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"'))



def string_to_identifier(s, white_space_becomes='_'):
    """ Takes a string and makes it suitable for use as an identifier

        Translates to lower case
        Replaces white space by the white_space_becomes character (default=underscore).
        Removes and punctuation.
    """
    import re
    s = s.lower()
    s = re.sub(r"\s+", white_space_becomes, s) # replace whitespace with underscores
    s = re.sub(r"-", "_", s) # replace hyphens with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "", s) # remove everything that's not a character, a digit or a _
    return s


if __name__ == "__main__":
    print (string_to_identifier("Pea\nsdf-43q45,.!@#%&@&@@24n  pijn  Kenter, hallo$"))



def replaceStringsInDict(obj, old, new):
    """ Recursively searches for a string in a dict and replaces a string by another
    """
    if isinstance(obj, dict):
        return {key: replaceStringsInDict(value, old, new) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replaceStringsInDict(value, old, new) for value in obj]
    elif is_a_string(obj):
        return obj.replace(old, new)
    else:
        return obj


def remove_process_serial_number(arg_list):
    """ Creates a copy of a list (typically sys.argv) where the strings that
        start with '-psn_0_' are removed.

        These are the process serial number used by the OS-X open command
        to bring applications to the front. They clash with argparse.
        See: http://hintsforums.macworld.com/showthread.php?t=11978
    """
    return [arg for arg in arg_list if not arg.startswith("-psn_0_")]


def replace_eol_chars(attr):
    """ Replace end-of-line characters with unicode glyphs so that all table rows fit on one line.
    """
    return (attr.replace('\r\n', unichr(0x21B5))
            .replace('\n', unichr(0x21B5))
            .replace('\r', unichr(0x21B5)))


def pformat(obj, width) -> str:
    """ Pretty print format with Argos default parameter values.
    """
    return pprint.pformat(obj, width=width, depth=2, sort_dicts=False)


def wrapHtmlColor(html, color):
    """ Wraps HTML in a span with a certain color
    """
    return '<span style="color:{}; white-space:pre;">{}</span>'\
        .format(color, escape(html, quote=False))

