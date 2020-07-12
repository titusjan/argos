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

from fnmatch import fnmatch

from argos.info import DEBUGGING
from argos.reg.basereg import BaseRegItem, BaseRegistry
from argos.utils.cls import check_is_a_string, check_class, check_is_a_sequence
from argos.utils.misc import prepend_point_to_extension

logger = logging.getLogger(__name__)


def parseExtensionStr(extensions):
    """ Splits extension string on colons and prepends points to each extension

        :returns: List of extensions
    """
    check_class(extensions, str)
    extensionList = extensions.split(':')
    return [prepend_point_to_extension(ext.strip()) for ext in extensionList]



class RtiRegItem(BaseRegItem):
    """ Class to keep track of a registered Repo Tree Item.
    """
    FIELDS =  BaseRegItem.FIELDS + ['globs']
    LABELS =  BaseRegItem.LABELS + ['Globs']

    def __init__(self, name='', absClassName='', pythonPath='', globs=''):
        """ Constructor. See the ClassRegItem class doc string for the parameter help.
        """
        super(RtiRegItem, self).__init__(name=name, absClassName=absClassName, pythonPath=pythonPath)

        check_class(globs, str)
        self._data['globs'] = globs

        # The following optimization works because self._data is not changed after creation. Only
        # when the uses is editing the plugins in the dialog is this not true, but then after
        # saving the entire registry is recreated.
        self._globList = self._data['globs'].split(':')


    def pathNameMatchesGlobs(self, path):
        """ Returns True if the file path matches one of the globs

            Matching is case-insensitive. See the Python fnmatch module for further info.
        """
        if DEBUGGING:
            check = self._globList = self._data['globs'].split(':')
            assert check == self._globList, "Sanity check failed: {} != {}"\
                .format(check, self._globList)

        for glob in self._globList:
            if fnmatch(path, glob.strip()):
                return True

        return False


    def getFileDialogFilter(self):
        """ Returns a filters that can be used to construct file dialogs filters,
            for example: 'Text File (*.txt;*.text)'
        """
        assert False, "TODO: reimplement"
        extStr = ';'.join(['*' + ext for ext in self.extensions])
        return '{} ({})'.format(self.name, extStr)




class RtiRegistry(BaseRegistry):
    """ Class that can be used to register repository tree items (RTIs).

        Maintains a name to RtiClass mapping and an extension to RtiClass mapping.
        The extension in the extensionToRti assure that a unique RTI is used as default mapping,
        the extensions in the RtiRegItem class do not have to be unique and are used in the
        filter in the getFileDialogFilter function.
    """
    ITEM_CLASS = RtiRegItem

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


    def getDefaultItems(self):
        """ Returns a list with the default plugins in the repo tree item registry.
        """

        # Note that when finding a plugin by extension, Argos uses the first one that matches.
        # Therefore put the defaults at the top of the list. The user can changed the order in the
        # plugin configuration dialog.

        hdfGlobs = '*.hdf5:*.h5:*.h5e:*.he5' # hdf extension is for HDF-4
        return [
            RtiRegItem('NetCDF file',
                       'argos.repo.rtiplugins.ncdf.NcdfFileRti',
                       globs='*.nc;*.nc4'),

            RtiRegItem('HDF-5 file',
                       'argos.repo.rtiplugins.hdf5.H5pyFileRti',
                       globs=hdfGlobs + ':*.nc'),

            RtiRegItem('NumPy binary file',
                       'argos.repo.rtiplugins.numpyio.NumpyBinaryFileRti',
                       globs='*.npy'),

            RtiRegItem('Pandas HDF file',
                       'argos.repo.rtiplugins.pandasio.PandasHdfFileRti',
                       globs=hdfGlobs),

            RtiRegItem('Pandas CSV file',
                       'argos.repo.rtiplugins.pandasio.PandasCsvFileRti',
                       globs='*.csv'),

            RtiRegItem('NumPy compressed file',
                       'argos.repo.rtiplugins.numpyio.NumpyCompressedFileRti',
                       globs='*.npz'),

            RtiRegItem('NumPy text file',
                       'argos.repo.rtiplugins.numpyio.NumpyTextFileRti',
                       #globs=['*.txt:*.text'),
                       globs='*.dat'),

            RtiRegItem('IDL save file',
                       'argos.repo.rtiplugins.scipyio.IdlSaveFileRti',
                       globs='*.sav'),

            RtiRegItem('MATLAB file',
                       'argos.repo.rtiplugins.scipyio.MatlabFileRti',
                       globs='*.mat'),

            RtiRegItem('Wav file',
                       'argos.repo.rtiplugins.scipyio.WavFileRti',
                       globs='*.wav'),

            RtiRegItem('Pillow image',
                       'argos.repo.rtiplugins.pillowio.PillowFileRti',
                       globs='*.bmp:*.eps:*.im:*.gif:*.jpg:*.jpeg:*.msp:*.pcx:*.png:*.ppm:*.spi:'
                             '*.tif:*.tiff:*.xbm:*.xv'),

            RtiRegItem('Exdir file',
                       'argos.repo.rtiplugins.exdir.ExdirFileRti',
                       globs='*.exdir'),

            # Add directory to the context menu so a an Exdir 'file' can be re-opened as a directory
            RtiRegItem('Directory',
                       'argos.repo.filesytemrtis.DirectoryRti',
                       globs=''),
        ]


# The RTI registry is implemented as a singleton. This is necessary because
# in DirectoryRti._fetchAllChildren we need access to the registry.
# TODO: think of an elegant way to access the ArgosApplication.registry from there.
# TODO: Make use of the lib.cls.Singleton mixin
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



