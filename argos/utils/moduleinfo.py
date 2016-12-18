""" Classes to gather information about modules for the About page

    These classes may be slightly over-engineered but they serve also as an experimentation ground
    for the plug-in mechanism. We therefore define both an interface (AbstractModuleInfo) and a
    read-only class that can be used as a base for descendants, just to see if this is practical.
"""
from __future__ import print_function

import sys
import logging

from abc import ABCMeta, abstractproperty

logger = logging.getLogger(__name__)

NOT_IMPLEMENTED_ERR_MSG = "You must override this abstract property/method."

class AbstractModuleInfo(object):
    """ Interface for the ModuleInfo classes
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        raise NotImplementedError(NOT_IMPLEMENTED_ERR_MSG)

    @abstractproperty
    def module(self):
        raise NotImplementedError(NOT_IMPLEMENTED_ERR_MSG)

    @abstractproperty
    def version(self):
        raise NotImplementedError(NOT_IMPLEMENTED_ERR_MSG)

    @abstractproperty
    def verboseVersion(self):
        raise NotImplementedError(NOT_IMPLEMENTED_ERR_MSG)

    @abstractproperty
    def packagePath(self):
        raise NotImplementedError(NOT_IMPLEMENTED_ERR_MSG)


class ReadOnlyModuleInfo(AbstractModuleInfo):
    """ Module information that can only set with the constructor.
        Most useful as a base class for descendants.
    """
    def __init__(self,
                 name='',
                 module=None,
                 version='',
                 verboseVersion='',
                 packagePath=''):

        self._name = name
        self._module = module
        self._version = version
        self._verboseVersion = verboseVersion
        self._packagePath = packagePath

    @property
    def name(self):
        return self._name

    @property
    def module(self):
        return self._module

    @property
    def version(self):
        return self._version

    @property
    def verboseVersion(self):
        return self._verboseVersion

    @property
    def packagePath(self):
        return self._packagePath



# It is impossible to derive from ReadOnlyModuleInfo and only define the setters. Python
# will give an error because it would violate the contract that the properties cannot be changed.
# Therefore we make a simple class, which uses attributes, to use for debugging.
class DuckTypingModuleInfo(object):
    """ Module information that can be written to after contstruction.
        Most useful for debugging purposes.

        Does not inherit from the interface but uses the duck-typing principle
    """
    def __init__(self, name,
                 module=None,
                 version='',
                 verboseVersion='',
                 packagePath=''):

        self.name = name
        self.module = module
        self.version = version
        self.verboseVersion = verboseVersion
        self.packagePath = packagePath



class PythonModuleInfo(ReadOnlyModuleInfo):

    def __init__(self):

        super(PythonModuleInfo, self).__init__('Python', module=None)
        self._version = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
        self._verboseVersion = sys.version.replace('\n', '')


class ImportedModuleInfo(ReadOnlyModuleInfo):
    """ Tries to import a module by name and retrieve information from it.
    """
    def __init__(self, name,
                 module=None,
                 verboseVersion=None,
                 versionAttribute='__version__',
                 pathAttribute='__path__'):

        super(ImportedModuleInfo, self).__init__(name, module = module)

        self._versionAttribute = versionAttribute
        self._pathAttribute = pathAttribute

        if module is None:
            self.tryImportModule(name)

        if verboseVersion is None:
            self._verboseVersion = self._version


    def tryImportModule(self, name):
        """ Imports the module and sets version information
            If the module cannot be imported, the version is set to empty values.
        """
        self._name = name
        try:
            import importlib
            self._module = importlib.import_module(name)
        except ImportError:
            self._module = None
            self._version = ''
            self._packagePath = ''
        else:
            if self._versionAttribute:
                self._version = getattr(self._module, self._versionAttribute, '???')
            if self._pathAttribute:
                self._packagePath = getattr(self._module, self._pathAttribute, '???')


#################
# Special cases #
#################


class H5pyModuleInfo(ImportedModuleInfo):

    def __init__(self):

        super(H5pyModuleInfo, self).__init__('h5py', versionAttribute=None)
        if self.module:
            self._version = self.module.version.version
            self._verboseVersion = ('{} (libhdf5: {})'
                                    .format(self._version, self.module.version.hdf5_version))


class NetCDF4ModuleInfo(ImportedModuleInfo):

    def __init__(self):

        super(NetCDF4ModuleInfo, self).__init__('netCDF4', pathAttribute=None)
        if self.module:
            self._verboseVersion = ('{} (libncdf4: {}, libhdf5: {})'
                                    .format(self._version,
                                            self.module.__netcdf4libversion__,
                                            self.module.__hdf5libversion__))


class PillowInfo(ImportedModuleInfo):

    def __init__(self):

        super(PillowInfo, self).__init__('PIL', versionAttribute='PILLOW_VERSION')
        self._name = 'pillow (PIL)'


class QtModuleInfo(ImportedModuleInfo):

    def __init__(self):
        import argos.qt.misc as qtmisc
        super(QtModuleInfo, self).__init__(name=qtmisc.QT_API_NAME, module=qtmisc,
                                           versionAttribute='PYQT_VERSION', pathAttribute=None)

        self._verboseVersion = qtmisc.PYQT_VERSION + " ("
        if qtmisc.QT_API:
            self._verboseVersion += "api {}, qtpy: {}, ".format(qtmisc.QT_API, qtmisc.QTPY_VERSION)
        self._verboseVersion += "Qt: {})".format(qtmisc.QT_VERSION)

