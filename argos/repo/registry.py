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

""" Defines a global RTI registry to register repository tree item plugins.
"""
import logging
import os.path

from fnmatch import fnmatch

from argos.info import DEBUGGING
from argos.reg.basereg import BaseRegItem, BaseRegistry, RegType
from argos.repo.iconfactory import RtiIconFactory
from argos.utils.cls import check_class, is_a_color_str

logger = logging.getLogger(__name__)

ICON_COLOR_UNDEF = RtiIconFactory.COLOR_UNDEF
ICON_COLOR_UNKNOWN = RtiIconFactory.COLOR_UNKNOWN
ICON_COLOR_ERROR = RtiIconFactory.COLOR_ERROR
ICON_COLOR_MEMORY = RtiIconFactory.COLOR_MEMORY

ICON_COLOR_EXDIR = '#00BBFF'
ICON_COLOR_H5PY = '#00EE88'
ICON_COLOR_NCDF4 = '#0088FF'
ICON_COLOR_NUMPY = '#987456'
ICON_COLOR_PANDAS = '#FB9A99'
ICON_COLOR_PILLOW = '#FF40FF'
ICON_COLOR_SCIPY = ICON_COLOR_NUMPY
ICON_COLOR_JSON = '#880088'



class RtiRegItem(BaseRegItem):
    """ Class to keep track of a registered Repo Tree Item.
    """
    FIELDS  = BaseRegItem.FIELDS[:1] + ['iconColor', 'globs'] + BaseRegItem.FIELDS[1:]
    TYPES   = BaseRegItem.TYPES[:1] + [RegType.ColorStr, RegType.String] + BaseRegItem.TYPES[1:]
    LABELS  = BaseRegItem.LABELS[:1] + ['Icon Color', 'Globs'] + BaseRegItem.LABELS[1:]
    STRETCH = BaseRegItem.STRETCH[:1] + [False, True] + BaseRegItem.STRETCH[1:]

    COL_DECORATION = 0  # Display Icon in the main column

    def __init__(self, name='', absClassName='', pythonPath='', iconColor=ICON_COLOR_UNDEF, globs=''):
        """ Constructor. See the ClassRegItem class doc string for the parameter help.
        """
        super(RtiRegItem, self).__init__(name=name, absClassName=absClassName, pythonPath=pythonPath)
        check_class(globs, str)
        assert is_a_color_str(iconColor), \
            "Icon color for {} is not a color string: {!r}".format(self, iconColor)

        self._data['iconColor'] = iconColor
        self._data['globs'] = globs

    def __str__(self):
        return "<RtiRegItem: {}>".format(self.name)

    @property
    def iconColor(self):
        """ Icon color hex string.
        """
        return self._data['iconColor']


    @property
    def globList(self):
        """ Returns list of globs by splitting the globs string at the colons (:).
        """
        return self._data['globs'].split(';')


    def pathNameMatchesGlobs(self, path):
        """ Returns True if the file path matches one of the globs

            Matching is case-insensitive. See the Python fnmatch module for further info.
        """
        for glob in self.globList:
            if DEBUGGING:
                logger.debug("  glob '{}' -> match = {}".format(glob, fnmatch(path, glob)))
            if fnmatch(path, glob):
                return True

        return False


    def getFileDialogFilter(self):
        """ Returns a filters that can be used to construct file dialogs filters,
            for example: 'Text File (*.txt;*.text)'
        """
        # Remove any path info from the glob. E.g. '/mypath/prefix*1.nc' becomes '*.nc'
        extensions = ['*' + os.path.splitext(glob)[1] for glob in self.globList]
        return '{} ({})'.format(self.name, ';'.join(extensions))


    @property
    def decoration(self):
        """ The displayed icon.
        """
        rtiIconFactory = RtiIconFactory.singleton()

        if self._exception:
            return rtiIconFactory.getIcon(
                rtiIconFactory.ERROR, isOpen=False, color=rtiIconFactory.COLOR_ERROR)
        else:
            if self._cls is None:
                return rtiIconFactory.getIcon(
                    rtiIconFactory.ERROR, isOpen=False, color=rtiIconFactory.COLOR_UNKNOWN)
            else:
                return rtiIconFactory.getIcon(
                    self.cls._defaultIconGlyph, isOpen=False, color=self.iconColor)





class RtiRegistry(BaseRegistry):
    """ Class that can be used to register repository tree items (RTIs).

        Maintains a name to RtiClass mapping and an extension to RtiClass mapping.
        The extension in the extensionToRti assure that a unique RTI is used as default mapping,
        the extensions in the RtiRegItem class do not have to be unique and are used in the
        filter in the getFileDialogFilter function.
    """
    ITEM_CLASS = RtiRegItem

    DIRECTORY_REG_ITEM = RtiRegItem('Directory', 'argos.repo.filesytemrtis.DirectoryRti',
                                    iconColor=ICON_COLOR_UNKNOWN)

    def __init__(self):
        """ Constructor
        """
        super(RtiRegistry, self).__init__()
        self._extensionMap = {}


    def getRtiRegItemByExtension(self, filePath):
        """ Returns the first RtiRegItem class where filePath matches one of the globs patherns.
            Returns None if no class registered for the extension.
        """
        # Current implementation just returns the first rtiRegItem that contains the extension.
        logger.debug("{} getRtiRegItemByExtension, filePath: {}".format(self, filePath))
        for rtiRegItem in self._items:
            if rtiRegItem.pathNameMatchesGlobs(filePath):
                return rtiRegItem

        return None


    def getFileDialogFilter(self):
        """ Returns a filter that can be used in open file dialogs,
            for example: 'All files (*);;Txt (*.txt;*.text);;netCDF(*.nc;*.nc4)'
        """
        filters = []
        for regRti in self.items:
            filters.append(regRti.getFileDialogFilter())
        return ';;'.join(filters)


    def extraItemsForOpenAsMenu(self):
        """ Creates list of RtiRegItem to append to the 'open-as' and 'reload-as menus
        """
        # Add directory to the context menu so a an Exdir 'file' can be re-opened as a directory
        return [self.DIRECTORY_REG_ITEM]


    def getDefaultItems(self):
        """ Returns a list with the default plugins in the repo tree item registry.
        """

        # Note that when finding a plugin by extension, Argos uses the first one that matches.
        # Therefore put the defaults at the top of the list. The user can changed the order in the
        # plugin configuration dialog.

        hdfGlobs = '*.hdf5;*.h5;*.h5e;*.he5' # hdf extension is for HDF-4
        return [
            RtiRegItem('HDF-5 file',
                       'argos.repo.rtiplugins.hdf5.H5pyFileRti',
                       iconColor=ICON_COLOR_H5PY,
                       globs=hdfGlobs),

            RtiRegItem('Exdir file',
                       'argos.repo.rtiplugins.exdir.ExdirFileRti',
                       iconColor=ICON_COLOR_EXDIR,
                       globs='*.exdir'),

            RtiRegItem('NetCDF file',
                       'argos.repo.rtiplugins.ncdf.NcdfFileRti',
                       iconColor=ICON_COLOR_NCDF4,
                       globs='*.nc;*.nc4'),

            RtiRegItem('Pandas HDF file',
                       'argos.repo.rtiplugins.pandasio.PandasHdfFileRti',
                       iconColor=ICON_COLOR_PANDAS,
                       globs=hdfGlobs),

            RtiRegItem('Pandas CSV file',
                       'argos.repo.rtiplugins.pandasio.PandasCsvFileRti',
                       iconColor=ICON_COLOR_PANDAS,
                       globs='*.csv'),

            RtiRegItem('NumPy binary file',
                       'argos.repo.rtiplugins.numpyio.NumpyBinaryFileRti',
                       iconColor=ICON_COLOR_NUMPY,
                       globs='*.npy'),

            RtiRegItem('NumPy compressed file',
                       'argos.repo.rtiplugins.numpyio.NumpyCompressedFileRti',
                       iconColor=ICON_COLOR_NUMPY,
                       globs='*.npz'),

            RtiRegItem('NumPy text file',
                       'argos.repo.rtiplugins.numpyio.NumpyTextFileRti',
                       iconColor=ICON_COLOR_NUMPY,
                       #globs=['*.txt;*.text'),
                       globs='*.dat'),

            RtiRegItem('IDL save file',
                       'argos.repo.rtiplugins.scipyio.IdlSaveFileRti',
                       iconColor=ICON_COLOR_SCIPY,
                       globs='*.sav'),

            RtiRegItem('MATLAB file',
                       'argos.repo.rtiplugins.scipyio.MatlabFileRti',
                       iconColor=ICON_COLOR_SCIPY,
                       globs='*.mat'),

            RtiRegItem('Wav file',
                       'argos.repo.rtiplugins.scipyio.WavFileRti',
                       iconColor=ICON_COLOR_SCIPY,
                       globs='*.wav'),

            RtiRegItem('Pillow image',
                       'argos.repo.rtiplugins.pillowio.PillowFileRti',
                       iconColor=ICON_COLOR_PILLOW,
                       globs='*.bmp;*.eps;*.im;*.gif;*.jpg;*.jpeg;*.msp;*.pcx;*.png;*.ppm;*.spi;'
                             '*.tif;*.tiff;*.xbm;*.xv'),

            RtiRegItem('JSON file',
                       'argos.repo.rtiplugins.jsonio.JsonFileRti',
                       iconColor=ICON_COLOR_JSON,
                       globs='*.json'),
        ]


# The RTI registry is implemented as a singleton. This is necessary because
# in DirectoryRti._fetchAllChildren we need access to the registry.
# TODO: think of an elegant way to access the ArgosApplication.registry from there.
# TODO: Make use of the lib.cls.Singleton mixin (or metaclass when Python 3)
def createGlobalRegistryFunction():
    """ Closure to create the RtiRegistry singleton
    """
    globReg = RtiRegistry()

    def accessGlobalRegistry():
        return globReg

    return accessGlobalRegistry

# This is actually a function definition, not a constant
#pylint: disable=C0103

globalRtiRegistry = createGlobalRegistryFunction()
globalRtiRegistry.__doc__ = "Function that returns the RtiRegistry singleton common to all windows"



