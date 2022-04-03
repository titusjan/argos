#!/usr/bin/env python
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
# along with Argos.  If not, see <http://www.gnu.org/licenses/>.

""" Argos numerical data inspector.
"""
from __future__ import print_function

# ----IMPORTANT ----
# Do not do any imports here that (indirectly) import any dependencies (PyQt, numpy, etc)
# The browse function is imported by the argos package, which in turn is imported by setup.py.
# If you import (for instance) numpy here, the setup.py will fail if numpy is not installed.
# Therefore, we do all imports from the argos package in the functions here.

import argparse
import logging
import os
import os.path
import sys

from glob import glob

logging.captureWarnings(True)

logger = logging.getLogger('argos')

logging.basicConfig(level='DEBUG', stream=sys.stderr,
                    #format='%(name)35s %(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s')
                    format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s')

# We are not using **kwargs here so IDEs can see which parameters are expected.
def browse(filePatterns=None, *,
           select=None,
           inspectorFullName=None,
           qtStyle=None,
           styleSheet=None,
           settingsFile=None,
           addTestData=False,
           runTestWalk=False):
    """ Opens the main window(s) for the persistent settings and executes the application.

        :param filePatterns: List of file names (or unix glob patterns like *.h5) that will be
            added to the repository. If only one file or directory is given it will be selected
            and expanded at start up.
        :param select: a path of the repository item that will selected and expanded at start up,
            even if more than one file or directory is given on the command line.
        :param inspectorFullName: The full path name of the inspector that will be loaded
        :param qtStyle: name of qtStyle (E.g. fusion).
        :param styleSheet: a path to an optional Qt Cascading Style Sheet.
        :param settingsFile: file with persistent settings. If None a default will be used.
        :param addTestData: if True, some in-memory test data is added to the repository tree.
        :param runTestWalk: if True, all nodes are visited and the program exits.
    """
    # Import in functions. See comments at the top for more details
    from argos.info import EXIT_CODE_RESTART

    # Creates and runs an ArgosApplication in a while loop to 'restart' application when the
    # plugin registry was edited.
    while True:
        logger.info("Starting browse window...")
        argosApplication = createArgosApp(
            filePatterns=filePatterns,
            select=select,
            inspectorFullName=inspectorFullName,
            qtStyle=qtStyle,
            styleSheet=styleSheet,
            settingsFile=settingsFile,
            addTestData=addTestData,
            runTestWalk=runTestWalk
        )

        exitCode = argosApplication.execute()

        logger.info("Argos finished with exit code: {}".format(exitCode))
        if exitCode != EXIT_CODE_RESTART:
            return exitCode
        else:
            logger.info("----- Restart requested. The Qt event loop will be restarted. -----\n")



def createArgosApp(filePatterns=None, *,
                   select=None,
                   inspectorFullName=None,
                   qtStyle=None,
                   styleSheet=None,
                   settingsFile=None,
                   addTestData=False,
                   runTestWalk=False):
    """ Creates an Argos application, including window(s) and loads the data.

       The Argos application will also create a QtApplication. You will have to call
       argosApp.execute() on the returned Argos application to start the Qt event loop.

        Returns:
            The newly created ArgosApplication object.
    """
    # Import in functions. See comments at the top for more details.
    from argos.info import DEBUGGING
    from argos.qt import QtWidgets, QtCore
    from argos.application import ArgosApplication
    from argos.repo.testdata import createArgosTestData
    from argos.utils.dirs import normRealPath
    from argos.widgets.misc import setApplicationQtStyle, setApplicationStyleSheet

    argosApp = ArgosApplication(settingsFile, runTestWalk=runTestWalk)
    argosApp.loadSettings(inspectorFullName)  # TODO: call in constructor?

    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    except Exception as ex:
        logger.debug("AA_UseHighDpiPixmaps not available in PyQt4: {}".format(ex))

    if qtStyle:
        availableStyles = QtWidgets.QStyleFactory.keys()
        if  qtStyle not in availableStyles:
            logger.warning("Qt style '{}' is not available on this computer. Use one of: {}"
                           .format(qtStyle, availableStyles))
        else:
            setApplicationQtStyle(qtStyle)

    if not os.path.exists(styleSheet):
        msg = "Stylesheet not found: {}".format(styleSheet)
        print(msg, file=sys.stderr)
        logger.warning(msg)
        #sys.exit(2)
    setApplicationStyleSheet(styleSheet)

    # Load data in common repository before windows are created.

    fileNames = [f for fp in filePatterns for f in glob(fp)]

    argosApp.loadFiles(fileNames)

    if addTestData:
        argosApp.repo.insertItem(createArgosTestData())

    if select:
        selectPath = select
        logger.debug("Using selection path from the command line: {!r}".format(selectPath))
    else:
        if len(fileNames) == 1:
            # Using normpath to remove trailing slashes.
            selectPath = os.path.basename(normRealPath(fileNames[0]))
            logger.debug("Selection path is the only file that is given on the command line: {!r}"
                         .format(selectPath))
        else:
            selectPath = None
            logger.debug("Not selecting any files (selection path = {!r})".format(selectPath))

    if selectPath:
        logger.debug("Selection path: {}".format(selectPath))
        for mainWindow in argosApp.mainWindows:
            mainWindow.trySelectRtiByPath(selectPath)

    return argosApp


def printInspectors(settingsFile):
    """ Prints a list of inspectors
    """
    # Imported here so this module can be imported without Qt being installed.
    from argos.application import ArgosApplication

    argosApp = ArgosApplication(settingsFile)
    argosApp.loadSettings(None)

    print("# Argos' registered inspectors")
    for regItem in argosApp.inspectorRegistry.items:
        print(regItem.name)


def main():
    """ Starts Argos main window
    """
    # Import in functions. See comments at the top for more details
    import numpy as np

    from argos.widgets.constants import NUMPY_LINE_WIDTH
    from argos.info import DEBUGGING, PROJECT_NAME, VERSION, EXIT_CODE_RESTART, resource_directory
    from argos.utils.logs import initLogging
    from argos.utils.misc import remove_process_serial_number

    aboutStr = "{} version: {}".format(PROJECT_NAME, VERSION)
    parser = argparse.ArgumentParser(description = aboutStr)

    parser.add_argument('-v', '--version', action = 'store_true',
        help="Prints the program version and exits")

    parser.add_argument('filePatterns', metavar='FILE', nargs='*',
        help="""Files or directories that will be loaded at start up. Accepts unix-like glob
                patterns, even on Windows. E.g.: 'argos *.h5' opens all files with the h5 extension
                in the current directory.""")

    parser.add_argument('-s', '--select', dest='selectPath',
        help="""Full path name of an item in the data tree that will be selected at start-up.
                E.g. 'file/var/fieldname'.""")

    parser.add_argument('-i', '--inspector', dest='inspector',
        help="""The name of the inspector that will be opened at start up. E.g. Table""")

    parser.add_argument('--list-inspectors', dest='list_inspectors', action = 'store_true',
        help="""Prints a list of available inspectors for the -i option, and exits.""")

    cfgGroup = parser.add_argument_group(
        "config options", description="Options related to style and configuration.")

    cfgGroup.add_argument('--qt-style', dest='qtStyle', help='Qt style. E.g.: fusion')

    cfgGroup.add_argument('--qss', dest='styleSheet',
                        help="Name of Qt Style Sheet file. If not set, the Argos default style "
                             "sheet will be used.")

    cfgGroup.add_argument('-c', '--config-file', metavar='FILE', dest='settingsFile',
        help="Configuration file with persistent settings. When using a relative path the settings "
             "file is loaded/saved to the argos settings directory.")

    cfgGroup.add_argument('--log-config', metavar='FILE', dest='logConfigFileName',
                        help='Logging configuration file. If not set a default will be used.')

    cfgGroup.add_argument('-l', '--log-level', dest='log_level', default='',
        help="Log level. If set, only log messages with a level higher or equal than this will be "
             "printed to screen (stderr). Overrides the log level of the StreamHandlers in the "
             "--log-config file. Does not alter the log level of log handlers that write to a "
             "file.",
        choices=('debug', 'info', 'warning', 'error', 'critical'))

    devGroup = parser.add_argument_group(
        "developer options", description="Options that are mainly useful for Argos developers.")

    devGroup.add_argument('-d', '--debugging-mode', dest='debugging', action = 'store_true',
        help="Run Argos in debugging mode. Useful during development.")

    devGroup.add_argument('--add-test-data', dest='addTestData', action = 'store_true',
        help="Adds some in-memory test data. Useful during development.")

    devGroup.add_argument('--run-test-walk', dest='runTestWalk', action = 'store_true',
        help="Walks through all the nodes in the repository tree and exits. "
             "The exit code 1 if any of the nodes failed to display.")

    args = parser.parse_args(remove_process_serial_number(sys.argv[1:]))

    initLogging(args.logConfigFileName, args.log_level)

    if args.version:
        print(aboutStr)
        sys.exit(0)

    if args.list_inspectors:
        printInspectors(args.settingsFile)
        sys.exit(0)

    logger.info("######################################")
    logger.info("####         Starting Argos       ####")
    logger.info("######################################")
    logger.info(aboutStr)

    logger.debug("argv: {}".format(sys.argv))
    logger.debug("Main argos module file: {}".format(__file__))
    logger.debug("PID: {}".format(os.getpid()))

    if DEBUGGING:
        logger.warning("Debugging flag is on!")

    logger.info('Started {} {}'.format(PROJECT_NAME, VERSION))
    logger.info("Python version: {}".format(sys.version).replace('\n', ''))

    # Imported here so this module can be imported without Qt being installed.
    from argos.qt.bindings import QT_API_NAME
    logger.info("Using {} Python Qt bindings".format(QT_API_NAME))

    # The DEBUGGING 'constant' is set before the arguments are parsed by argparse.
    # Sanity check for consistency.
    assert args.debugging == DEBUGGING, ("Inconsistent debugging mode. {} != {}"
                                         .format(args.debugging, DEBUGGING))

    qtStyle = args.qtStyle if args.qtStyle else os.environ.get("QT_STYLE_OVERRIDE", 'Fusion')
    styleSheet = args.styleSheet if args.styleSheet else os.environ.get("ARGOS_STYLE_SHEET", '')

    if not styleSheet:
        styleSheet = os.path.join(resource_directory(), "argos.css")
        logger.debug("Using default style sheet: {}".format(styleSheet))
    else:
        styleSheet = os.path.abspath(styleSheet)

    logger.debug("Setting numpy line width to {} characters".format(NUMPY_LINE_WIDTH))
    np.set_printoptions(linewidth=NUMPY_LINE_WIDTH)

    # Browse will create an ArgosApplication with one MainWindow
    browse(filePatterns = args.filePatterns,
           inspectorFullName=args.inspector,
           select=args.selectPath,
           qtStyle=qtStyle,
           styleSheet=styleSheet,
           settingsFile=args.settingsFile,
           addTestData=args.addTestData,
           runTestWalk=args.runTestWalk)
    logger.info('Done {}'.format(PROJECT_NAME))

if __name__ == "__main__":
    main()

