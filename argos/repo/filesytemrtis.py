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

""" Repository items (RTIs) for browsing the file system
"""
import logging, os
from argos.repo.baserti import BaseRti
from argos.repo.iconfactory import RtiIconFactory
from argos.repo.registry import globalRtiRegistry, ICON_COLOR_UNKNOWN

logger = logging.getLogger(__name__)


class UnknownFileRti(BaseRti):
    """ A repository tree item that represents a file of unknown type.
        The file is not opened.
    """
    _defaultIconGlyph = RtiIconFactory.FILE

    def __init__(self, nodeName='', iconColor=ICON_COLOR_UNKNOWN, fileName=''):
        """ Constructor
        """
        super(UnknownFileRti, self).__init__(
            nodeName=nodeName, iconColor=iconColor, fileName=fileName)

        self._checkFileExists()


    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False



class DirectoryRti(BaseRti):
    """ A directory in the repository data tree.
    """
    _defaultIconGlyph = RtiIconFactory.FOLDER
    _defaultIconColor = RtiIconFactory.COLOR_UNKNOWN

    def __init__(self, nodeName='', iconColor=ICON_COLOR_UNKNOWN, fileName=''):
        """ Constructor
        """
        super(DirectoryRti, self).__init__(
            nodeName=nodeName, iconColor=iconColor, fileName=fileName)
        self._checkFileExists() # TODO: check for directory?


    def _fetchAllChildren(self):
        """ Gets all sub directories and files within the current directory.
            Does not fetch hidden files.
        """
        childItems = []
        fileNames = sorted(os.listdir(self._fileName), key=lambda s: s.lower())
        absFileNames = [os.path.join(self._fileName, fn) for fn in fileNames]

        for fileName, absFileName in zip(fileNames, absFileNames):
            if not fileName.startswith('.'):
                childItem = createRtiFromFileName(absFileName)
                childItems.append(childItem)

        return childItems


def _detectRtiFromFileName(fileName):
    """ Determines the type of RepoTreeItem to use given a file or directory name.
        Uses a DirectoryRti for directories without a registered extension and an UnknownFileRti
        if the file extension doesn't match one of the registered RTI globs.

        Returns (cls, regItem) tuple. Both the cls ond the regItem can be None.
        If the file is a directory without a registered extension, (DirectoryRti, None) is returned.
        If the file extension is not in the registry, (UnknownFileRti, None) is returned.
        If the cls cannot be imported (None, regItem) returned. regItem.exception will be set.
        Otherwise (cls, regItem) will be returned.

         Note that directories can have an extension (e.g. extdir archives). So it is not enough to
         just test if a file is a directory.
    """
    #_, extension = os.path.splitext(os.path.normpath(fileName))
    fullPath = os.path.normpath(os.path.abspath(fileName))
    rtiRegItem = globalRtiRegistry().getRtiRegItemByExtension(fullPath)
    if rtiRegItem is None:
        if os.path.isdir(fileName):
            cls = DirectoryRti
        else:
            logger.debug("No file RTI registered for path: {}".format(fullPath))
            cls = UnknownFileRti
    else:
         cls = rtiRegItem.getClass(tryImport=True) # cls can be None

    return cls, rtiRegItem


def createRtiFromFileName(fileName):
    """ Determines the type of RepoTreeItem to use given a file or directory name and creates it.
        Uses a DirectoryRti for directories without registered extensions and an UnknownFileRti if the file
        extension doesn't match one of the registered RTI extensions.
    """
    cls, rtiRegItem = _detectRtiFromFileName(fileName)
    assert not (cls is None and rtiRegItem is None), "cls and rtiRegItem both none."

    iconColor = rtiRegItem.iconColor if rtiRegItem else ICON_COLOR_UNKNOWN

    if cls is None:
        logger.warning("Unable to import plugin {}: {}"
                       .format(rtiRegItem.name, rtiRegItem.exception))
        rti = UnknownFileRti.createFromFileName(fileName, ICON_COLOR_UNKNOWN)
        rti.setException(rtiRegItem.exception)
    else:
        logger.debug("Calling createFromFileName: {} ({}, {})".format(cls, fileName, iconColor))
        rti = cls.createFromFileName(fileName, iconColor)

    assert rti, "Sanity check failed (createRtiFromFileName). Please report this bug."

    return rti

