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
from libargos.selector.abstractstore import (BaseRti, LazyLoadRtiMixin)

logger = logging.getLogger(__name__)


# TODO: merge with OpenFileRti? Then rename to FileRti

class ClosedFileRti(BaseRti):
    """ A repository tree item that has a reference to a file. 
    """
    def __init__(self, fileName, nodeName=None):
        """ Constructor 
        """
        BaseRti.__init__(self, nodeName=nodeName)
        fileName = os.path.realpath(fileName) 
        assert os.path.isfile(fileName), "Not a regular file: {}".format(fileName)
        self._fileName = fileName
        
    @property
    def fileName(self):
        """ Returns the name of the underlying the file. 
        """
        return self._fileName


class OpenFileRti(BaseRti):
    """ A repository tree item that has a reference to a file. 
    """
    def __init__(self, fileName, nodeName=None):
        """ Constructor 
        """
        BaseRti.__init__(self, nodeName=nodeName)
        fileName = os.path.realpath(fileName) 
        assert os.path.isfile(fileName), "Not a regular file: {}".format(fileName)
        self._fileName = fileName
        
    @property
    def fileName(self):
        """ Returns the name of the underlying the file. 
        """
        return self._fileName


class DirectoryRti(LazyLoadRtiMixin, BaseRti):
    """ A repository tree item that has a reference to a file. 
    """
    def __init__(self, dirName, nodeName=None):
        """ Constructor
        """
        LazyLoadRtiMixin.__init__(self)
        BaseRti.__init__(self, nodeName=nodeName)

        dirName = os.path.realpath(dirName)
        assert os.path.isdir(dirName), "Not a directory: {}".format(dirName)
        self._fileName = dirName

        self._childrenFetched = False

        
    @property
    def fileName(self):
        """ Returns the name of the underlying the file. 
        """
        return self._fileName
    
        
    def _fetchAllChildren(self):
        """ Gets all sub directories and files within the current directory.
            Does not fetch hidden files.
        """
        childItems = []
        fileNames = os.listdir(self._fileName)
        absFileNames = [os.path.join(self._fileName, fn) for fn in fileNames]

        # Add subdirectories
        for fileName, absFileName in zip(fileNames, absFileNames):
            if os.path.isdir(absFileName) and not fileName.startswith('.'):
                childItems.append(DirectoryRti(absFileName, nodeName=fileName))
            
        # Add regular files
        for fileName, absFileName in zip(fileNames, absFileNames):
            if os.path.isfile(absFileName) and not fileName.startswith('.'):
                childItems.append(ClosedFileRti(absFileName, nodeName=fileName))
                        
        return childItems
    
        
    @classmethod
    def createFromFileName(cls, dirName):
        """ Creates a OpenFileRtiMixin (or descendant), given a file name.
        """
        # See https://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
        return cls(dirName, nodeName=os.path.basename(dirName))
    
    