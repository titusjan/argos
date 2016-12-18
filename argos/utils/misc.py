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


def log_dictionary(dictionary, msg='', logger=None, level='debug', item_prefix='  '):
    """ Writes a log message with key and value for each item in the dictionary.

        :param dictionary: the dictionary to be logged
        :type dictionary: dict
        :param name: An optional message that is logged before the contents
        :type name: string
        :param logger: A logging.Logger object to log to. If not set, the 'main' logger is used.
        :type logger: logging.Logger or a string
        :param level: log level. String or int as described in the logging module documentation.
            Default: 'debug'.
        :type level: string or int
        :param item_prefix: String that will be prefixed to each line. Default: two spaces.
        :type item_prefix: string
    """
    level_nr = logging.getLevelName(level.upper())

    if logger is None:
        logger = logging.getLogger('main')

    if msg :
        logger.log(level_nr, "Logging dictionary: {}".format(msg))

    if not dictionary:
        logger.log(level_nr,"{}<empty dictionary>".format(item_prefix))
        return

    max_key_len = max([len(k) for k in dictionary.keys()])

    for key, value in sorted(dictionary.items()):
        logger.log(level_nr, "{0}{1:<{2}s} = {3}".format(item_prefix, key, max_key_len, value))



def prepend_point_to_extension(extension):
    """ Prepends a point to the extension of it doesn't already start with it
    """
    if extension.startswith('.'):
        return extension
    else:
        return '.' + extension


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



