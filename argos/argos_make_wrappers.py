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

""" Create batch file wrappers so that Argos can be called from outside a (conda) environment.

    An alternative may be to use exec-wrappers.
        https://pypi.org/project/exec-wrappers/
        https://stackoverflow.com/questions/42025173/best-way-to-execute-a-python-script-in-a-given-conda-environment
"""
from __future__ import print_function

import argparse
import logging
import os.path
import sys

from argos.info import DEBUGGING, VERSION
from argos.utils.logs import make_log_format, initLogging
from argos.utils.misc import remove_process_serial_number

APP_NAME = 'argos_make_wrappers'

logger = logging.getLogger("argos." + APP_NAME)

logging.basicConfig(level='INFO', stream=sys.stderr, format=make_log_format())


def eprint(*args, **kwargs):
    """ Print to stderr
    """
    print(*args, file=sys.stderr, **kwargs)



def exitIfNotExists(fileName, prefix="File", postFix=""):
    """ Exits the program if the fileName does not exist.
    """
    if not os.path.exists(fileName):
        eprint("{} doesn't exist: '{}'. {}".format(prefix, fileName, postFix))
        sys.exit(1)


def exitIfNotAFile(fileName, prefix="File", postFix=""):
    """ Exits the program if the fileName does not exist or is a directory
    """
    exitIfNotExists(fileName, prefix, postFix)
    if os.path.isdir(fileName):
        eprint("{} is a directory: '{}. {}'".format(prefix, fileName, postFix))
        sys.exit(1)


def exitIfNotADir(fileName, prefix="File", postFix=""):
    """ Exits the program if the fileName does not exist or is NOT a directory
    """
    exitIfNotExists(fileName, prefix, postFix)
    if not os.path.isdir(fileName):
        eprint("{} is not a directory: '{}. {}'".format(prefix, fileName, postFix))
        sys.exit(1)


# C:\Users\kenter\Miniconda3\Scripts\conda.exe run -n argosdev C:\Users\kenter\Miniconda3\envs\argosdev\Scripts\argos.exe %*
TEMPLATE = r"""@rem Batch file for starting Argos from outside this Anaconda environment.
@rem Created with {appName}

@{condaExecutable} run -n {condaEnvironment} {argosExecutable} %*
"""

def writeScript(fileName, text, dryRun=False):
    """ Creates and writes the text to a wrapper script named fileName.

        If dryRun is True, no files are created but the scripts contents are printed on stdout.
    """
    if dryRun:
        logger.info("Simulate creating argos wrapper: {}".format(fileName))
        print("==== {} ====".format(fileName))
        print(text)
        print()
    else:
        logger.info("Creating argos wrapper: {}".format(fileName))
        with open(fileName, 'w') as fileOut:
            print(text, file=fileOut)


def makeCondaWrappers(dryRun=False, condaEnvironment=None, condaPrefix=None, condaExecutable=None):
    """ Creates wrapper batch scripts for Anaconda.
    """
    if dryRun:
        logger.warning("Not creating wrappers but printing to stdout instead.")

    logger.debug("Anaconda environment variables found:")
    for key, value in os.environ.items():
        if key.startswith('CONDA'):
            logger.debug("    {:25s} = {}".format(key, value))

    if condaEnvironment:
        logger.debug("Using conda environment name specified with the command line argument.")
    else:
        logger.debug("Using conda environment name from the CONDA_DEFAULT_ENV environment variable.")
        try:
            condaEnvironment = os.environ['CONDA_DEFAULT_ENV']
        except KeyError:
            eprint("CONDA_DEFAULT_ENV environment variable not found.")
            sys.exit(1)
    logger.info("Conda environment: '{}'".format(condaEnvironment))

    if condaPrefix:
        logger.debug("Using conda prefix specified with the command line argument.")
    else:
        logger.debug("Using conda prefix from the CONDA_PREFIX environment variable.")
        try:
            condaPrefix = os.environ['CONDA_PREFIX']
        except KeyError:
            eprint("CONDA_PREFIX environment variable not found.")
            sys.exit(1)
    logger.info("Conda prefix: '{}'".format(condaPrefix))
    exitIfNotADir(condaPrefix, "\nThe conda prefix",
                  "\n\nYou can use the --conda-prefix command line argument to specify it.")

    if condaEnvironment != "base" and not condaPrefix.endswith(condaEnvironment):
        logger.warning("Conda prefix ({}) does not end with conda environment ({})."
                       .format(condaPrefix, condaEnvironment))

    if condaExecutable:
        logger.debug("Using conda executable specified with the command line argument.")
    else:
        logger.debug("Using conda executable from the CONDA_EXE environment variable.")
        try:
            condaExecutable = os.environ['CONDA_EXE']
        except KeyError:
            eprint("CONDA_EXE environment variable not found.")
            sys.exit(1)

    condaExecutable = os.path.abspath(condaExecutable)
    logger.info("Conda executable: '{}'".format(condaExecutable))
    exitIfNotAFile(condaExecutable, "\nThe conda executable",
                   "\n\nYou can use the --conda-exe command line argument to specify it.")

    condaScriptsDir = os.path.join(condaPrefix, "Scripts")
    exitIfNotADir(condaScriptsDir, "\nThe conda Scripts dir")

    for argosBaseName in ['argos', 'argosw']:

        argosBasePath = os.path.normpath(os.path.join(condaScriptsDir, argosBaseName))
        argosExecutable = "{}.exe".format(argosBasePath)
        logger.debug("Argos executable: {}".format(argosExecutable))
        if not os.path.exists(argosExecutable):
            logger.warning("Argos executable does not exist: '{}'".format(argosExecutable))

        argosWrapper = "{}.bat".format(argosBasePath)

        text = TEMPLATE.format(
            appName=APP_NAME,
            condaExecutable=condaExecutable,
            argosExecutable=argosExecutable,
            condaEnvironment=condaEnvironment)

        writeScript(argosWrapper, text, dryRun=dryRun)



def main():
    """ Create batch file wrappers so that Argos can be called from outside a (conda) environment.
    """
    aboutStr = "{} version: {}".format("argos_make_wrappers", VERSION)
    parser = argparse.ArgumentParser(description = __doc__)

    parser.add_argument('-d', '--dry-run', dest='dryRun', action = 'store_true',
        help="""If set, no wrapper files are created but their contents is printed on stdout.""")

    parser.add_argument('--env', '--conda-env', dest='condaEnvironment',
        help="""Anaconda environment name, e.g. "base". If not given, the script tries to find it
                with the use of the environment variables in the current Anaconda environment.""")

    parser.add_argument('--prefix', '--conda-prefix', dest='condaPrefix',
        help=r"""Path to the Anaconda environment, e.g. "C:\Users\my_name\Miniconda3".
                If not given, the script tries to find it with the use of the environment variables
                in the current Anaconda environment.""")

    parser.add_argument('--exe', '--conda-exe', dest='condaExecutable',
        help="""Full path to the conda.exe executable. If not given, the script tries to find it
                with the use of the environment variables in the current Anaconda environment.""")

    parser.add_argument('-l', '--log-level', dest='log_level', default='info',
        help="Log level. If set, only log messages with a level higher or equal than this will be "
             "printed to screen (stderr). Overrides the log level of the StreamHandlers in the "
             "--log-config file. Does not alter the log level of log handlers that write to a "
             "file.",
        choices=('debug', 'info', 'warning', 'error', 'critical'))

    parser.add_argument('--version', action = 'store_true',
        help="Prints the program version and exits")

    args = parser.parse_args(remove_process_serial_number(sys.argv[1:]))

    initLogging(None, args.log_level)

    if args.version:
        print(aboutStr)
        sys.exit(0)

    logger.info(aboutStr)
    logger.debug("argv: {}".format(sys.argv))
    logger.debug("PID: {}".format(os.getpid()))

    makeCondaWrappers(
        dryRun=args.dryRun,
        condaExecutable=args.condaExecutable,
        condaPrefix=args.condaPrefix,
        condaEnvironment=args.condaEnvironment
    )

    logger.info('Done {}'.format(APP_NAME))

if __name__ == "__main__":
    main()

