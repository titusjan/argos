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
import logging
import pprint
import re

from html import escape
from typing import TypeVar, List, Any, Dict

from argos.utils.cls import isAString

logger = logging.getLogger(__name__)

class NotSpecified():
    """ Class for the NOT_SPECIFIED constant.
        Is used so that a parameter can have a default value other than None.

        Evaluates to False when converted to boolean.
    """
    def __bool__(self) -> bool:
        """ Always returns False. Called when converting to bool in Python 3.
        """
        return False

NOT_SPECIFIED = NotSpecified()


def isQuoted(s: str) -> bool:
    """ Returns True if the string begins and ends with quotes (single or double).
    """
    return (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"'))


def stringToIdentifier(s: str, white_space_becomes: str = '_') -> str:
    """ Takes a string and makes it suitable for use as an identifier.

        Translates to lower case.
        Replaces white space by the white_space_becomes character (default=underscore).
        Removes and punctuation.
    """
    s = s.lower()
    s = re.sub(r"\s+", white_space_becomes, s) # replace whitespace with underscores
    s = re.sub(r"-", "_", s) # replace hyphens with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "", s) # remove everything that's not a character, a digit or a _
    return s


T = TypeVar('T', Dict[Any, Any], List[Any], str)
def replaceStringsInDict(obj: T, old: str, new: str) -> T:
    """ Recursively searches for a string in a dict and replaces a string by another.
    """
    if isinstance(obj, dict):
        return {key: replaceStringsInDict(value, old, new) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replaceStringsInDict(value, old, new) for value in obj]
    elif isAString(obj):
        return obj.replace(old, new)
    else:
        return obj


def removeProcessSerialNumber(argList: List[str]) -> List[str]:
    """ Creates a copy of a list (typically sys.argv) where the strings that
        start with ``-psn_0_`` are removed.

        These are the process serial number used by the OS-X open command
        to bring applications to the front. They clash with argparse.
        See: http://hintsforums.macworld.com/showthread.php?t=11978
    """
    return [arg for arg in argList if not arg.startswith("-psn_0_")]


def replaceEolChars(attr: str) -> str:
    """ Replace end-of-line characters with unicode glyphs so that all table rows fit on one line.
    """
    return (attr.replace('\r\n', chr(0x21B5))
            .replace('\n', chr(0x21B5))
            .replace('\r', chr(0x21B5)))


def pformat(obj: Any, width: int) -> str:
    """ Pretty print format with Argos default parameter values.
    """
    return pprint.pformat(obj, width=width, depth=2, sort_dicts=False)


def wrapHtmlColor(html: str, color: str) -> str:
    """ Wraps HTML in a span with a certain color
    """
    return '<span style="color:{}; white-space:pre;">{}</span>'\
        .format(color, html)

