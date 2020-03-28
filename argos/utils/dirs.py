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

r""" Default config and log directories under the different platforms.

    Config files are stored in a subdirectory of the genericConfigLocation. Log files are stored
    in a sub directory of the genericLocalDataLocation. These are:

        Windows:
            baseConfigLocation    -> C:\Users\<user>\AppData\Local\
            baseLocalDataLocation -> C:\Users\<user>\AppData\Local\

        OS-X:
            baseConfigLocation    -> ~/Library/Preferences
            baseLocalDataLocation -> ~/Library/Application Support

        Linux:
            baseConfigLocation    -> ~/.config
            baseLocalDataLocation -> ~/.local/share

    See http://doc.qt.io/qt-5/qsettings.html#platform-specific-notes.

"""

import logging
import os.path
import platform

from argos.info import ORGANIZATION_NAME, SCRIPT_NAME

logger  = logging.getLogger(__name__)


def normRealPath(path):
    """ Returns the normalized real path.

        If the path is empty or None it is returned as-is. This is to prevent expanding to the
        current directory in case of undefined paths.
    """
    if path:
        return os.path.normpath(os.path.realpath(path))
    else:
        return path


def ensureDirectoryExists(dirName):
    """ Creates a directory if it doesn't yet exist.
    """
    if not os.path.exists(dirName):
        logger.info("Creating directory: {}".format(normRealPath(dirName)))
        os.makedirs(dirName)


def ensureFileExists(pathName):
    """ Creates an empty file file if it doesn't yet exist. Also creates necessary directory path.

        :returns: the normRealPath of the path name.
    """
    pathName = normRealPath(pathName)
    dirName, fileName = os.path.split(pathName)
    ensureDirectoryExists(dirName)

    if not os.path.exists(pathName):
        logger.info("Creating empty file: {}".format(pathName))
        with open(pathName, 'w') as f:
            f.write('')

    # Check file exists and is not a directory.
    assert os.path.isfile(pathName), "File does not exist or is a directory: {!r}".format(pathName)
    return pathName


def homeDirectory():
    """ Returns the user's home directory.

        https://stackoverflow.com/a/4028943/625350
    """
    return os.path.expanduser("~")





################
# Config files #
################


def baseConfigLocation():
    r""" Gets the base configuration directory (for all applications of the user).

        See the module doc string at the top for details.
    """
    # Same as QtCore.QStandardPaths.AppConfigLocation, but without having to import Qt
    sysName = platform.system()

    if sysName == "Darwin":
        configDir = os.path.join(homeDirectory(), 'Library', 'Preferences')
    elif sysName == "Linux":
        configDir = os.path.join(homeDirectory(), '.config')
    elif sysName == "Windows":
        configDir = os.environ.get("LOCALAPPDATA", os.path.join(homeDirectory(), 'AppData', 'Local'))
    else:
        raise AssertionError("Unknown Operating System: {}".format(sysName))

    assert configDir, "No baseConfigLocation found."
    return normRealPath(configDir)


def argosConfigDirectory():
    r""" Gets the Argos configuration directory.

        The config directory is platform dependent. (See the module doc string at the top).
    """
    return os.path.join(baseConfigLocation(), ORGANIZATION_NAME, SCRIPT_NAME)

#
# def appConfigFileName(configFile):
#     """ Returns default config file if configFile is emtpy string or None
#     """
#     if configFile:
#         # Config file specified on the command line
#         return configFile
#     else:
#         # Use the default config file name
#         configDir = argosConfigDirectory()
#         configFile = normRealPath(os.path.join(configDir, 'config.yaml'))
#         return configFile



#############
# Log files #
#############


def baseLocalDataLocation():
    r""" Gets the base configuration directory (for all applications of the user).

        The config directory is platform dependent (see the Qt documentation for baseDataLocation).
        On Windows this will be something like:
            C:\Users\<user>\AppData\Local\

        See the module doc string at the top for details.
    """
    # Same as QtCore.QStandardPaths.AppConfigLocation, but without having to import Qt
    sysName = platform.system()

    if sysName == "Darwin":
        cfgDir = os.path.join(homeDirectory(), 'Library', 'Application Support')
    elif sysName == "Linux":
        cfgDir = os.path.join(homeDirectory(), '.local', 'share')
    elif sysName == "Windows":
        cfgDir = os.environ.get("APPLOCALDATA2", os.path.join(homeDirectory(), 'AppData', 'Local'))
    else:
        raise AssertionError("Unknown Operating System: {}".format(sysName))

    assert cfgDir, "No baseConfigLocation found."
    return normRealPath(cfgDir)


def argosLocalDataDirectory():
    r""" Returns a directory where Argos can store files locally (not roaming).

        This directory is platform dependent. (See the module doc string at the top).
    """
    return os.path.join(baseLocalDataLocation(), ORGANIZATION_NAME, SCRIPT_NAME)



def argosLogDirectory():
    r""" Returns the directory where Argos can store its log files.

        This is the 'logs' subdirectory of the argosLocalDataDirectory()
    """
    return os.path.join(argosLocalDataDirectory(), 'logs')



