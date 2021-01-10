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
# Therefore we do all imports from the argos package in the functions here.

import argparse
import glob
import logging
import os
import os.path
import sys

logging.captureWarnings(True)


logger = logging.getLogger('argos')

logging.basicConfig(level='DEBUG', stream=sys.stderr,
                    #format='%(name)35s %(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s')
                    format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s')

# We are not using **kwargs here so IDEs can see which parameters are expected.
def browse(fileNames=None,
           select=None,
           inspectorFullName=None,
           qtStyle=None,
           styleSheet=None,
           settingsFile=None):
    """ Opens the main window(s) for the persistent settings and executes the application.

        Calls _browse() in a while loop to enable pseudo restarts in case the registry was edited.

        :param fileNames: List of file names that will be added to the repository
        :param select: a path of the repository item that will selected at start up.
            Overrides 'open' parameter.
        :param inspectorFullName: The full path name of the inspector that will be loaded
        :param qtStyle: name of qtStyle (E.g. fusion).
        :param styleSheet: a path to an optional Qt Cascading Style Sheet.
        :param settingsFile: file with persistent settings. If None a default will be used.
    """
    # Import in functions. See comments at the top for more details
    from argos.info import EXIT_CODE_RESTART

    while True:
        logger.info("Starting browse window...")
        exitCode = _browse(
            fileNames=fileNames,
            select=select,
            inspectorFullName=inspectorFullName,
            qtStyle=qtStyle,
            styleSheet=styleSheet,
            settingsFile=settingsFile)

        logger.info("Argos finished with exit code: {}".format(exitCode))
        if exitCode != EXIT_CODE_RESTART:
            return exitCode
        else:
            logger.info("----- Restart requested. The Qt event loop will be restarted. -----\n")



def _browse(fileNames=None,
            select=None,
            inspectorFullName=None,
            qtStyle=None,
            styleSheet=None,
            settingsFile=None):
    """ Execute browse a single time
    """
    # Import in functions. See comments at the top for more details.
    from argos.info import DEBUGGING
    from argos.qt import QtWidgets, QtCore
    from argos.application import ArgosApplication
    from argos.repo.testdata import createArgosTestData
    from argos.widgets.misc import setApplicationQtStyle, setApplicationStyleSheet

    argosApp = ArgosApplication(settingsFile)
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
    argosApp.loadFiles(fileNames)

    if DEBUGGING:
        argosApp.repo.insertItem(createArgosTestData())

    if select:
        for mainWindow in argosApp.mainWindows:
            mainWindow.trySelectRtiByPath(select)

    return argosApp.execute()


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
    from argos.info import DEBUGGING, PROJECT_NAME, VERSION, EXIT_CODE_RESTART, resource_directory
    from argos.utils.logs import initLogging
    from argos.utils.misc import remove_process_serial_number

    aboutStr = "{} version: {}".format(PROJECT_NAME, VERSION)
    parser = argparse.ArgumentParser(description = aboutStr)

    parser.add_argument('fileNames', metavar='FILE', nargs='*',
        help="""Files or directories that will be loaded at start up. Accepts unix-like glob
                patterns, even on Windows. E.g.: 'argos *.h5' opens all files with the h5 extension
                in the current directory.""")

    parser.add_argument('-o', '--open', dest='openFile',
        help="""File or directory that will be loaded and selected at start-up.""")

    parser.add_argument('-s', '--select', dest='selectPath',
        help="""Full path name of an item in the data tree that will be selected at start-up.
                E.g. 'file/var/fieldname'. Overrides -o option.""")

    parser.add_argument('-i', '--inspector', dest='inspector',
        help="""The name of the inspector that will be opened at start up. E.g. Table""")

    parser.add_argument('--list-inspectors', dest='list_inspectors', action = 'store_true',
        help="""Prints a list of available inspectors for the -i option, and exits.""")

    parser.add_argument('--qt-style', dest='qtStyle', help='Qt style. E.g.: fusion')

    parser.add_argument('--qss', dest='styleSheet',
                        help="Name of Qt Style Sheet file. If not set, the Argos default style "
                             "sheet will be used.")

    parser.add_argument('-c', '--config-file', metavar='FILE', dest='settingsFile',
        help="Configuration file with persistent settings. When using a relative path the settings "
             "file is loaded/saved to the argos settings directory.")

    parser.add_argument('-d', '--debugging-mode', dest='debugging', action = 'store_true',
        help="Run Argos in debugging mode. Useful during development.")

    parser.add_argument('--log-config', dest='logConfigFileName',
                        help='Logging configuration file. If not set a default will be used.')

    parser.add_argument('-l', '--log-level', dest='log_level', default='',
        help="Log level. If set, only log messages with a level higher or equal than this will be "
             "printed to screen (stderr). Overrides the log level of the StreamHandlers in the "
             "--log-config file. Does not alter the log level of log handlers that write to a "
             "file.",
        choices=('debug', 'info', 'warning', 'error', 'critical'))

    parser.add_argument('--version', action = 'store_true',
        help="Prints the program version and exits")

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

    # Process -o option. Don't do this in browse. In the future we might be able to call browse()
    # from IPython. Decide at that point how to best pass these parameters.
    fileNames = []
    for fileName in args.fileNames:
        fileNames.extend(glob.glob(fileName))
    if args.openFile and args.openFile not in fileNames:
        fileNames.insert(0, args.openFile)

    if args.openFile and not args.selectPath:
        selectPath = os.path.basename(args.openFile)
    else:
        selectPath = args.selectPath

    # Browse will create an ArgosApplication with one MainWindow
    browse(fileNames = fileNames,
           inspectorFullName=args.inspector,
           select=selectPath,
           qtStyle=qtStyle,
           styleSheet=styleSheet,
           settingsFile=args.settingsFile)
    logger.info('Done {}'.format(PROJECT_NAME))

if __name__ == "__main__":
    main()

