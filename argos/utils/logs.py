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

r""" Various functions related to logging.
"""
import logging
import logging.config
import os.path
import json

from typing import List, Union, Dict, Any

from argos.utils.dirs import ensureDirectoryExists, normRealPath, argosLogDirectory
from argos.utils.misc import replaceStringsInDict

logger = logging.getLogger(__name__)


THIS_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

def findStreamHandlersInConfig() -> List[logging.Handler]:
    """ Searches for a handlers with 'stream' their name. Returns a list of handlers.
    """
    rootLogger = logging.getLogger()
    #logger.debug("Searching for Handlers in the root logger having 'stream' in their name")
    foundHandlers = []
    for handler in rootLogger.handlers:
        #logger.debug("  handler name: {}".format(handler.name))
        if handler.name and 'stream' in handler.name.lower():
            foundHandlers.append(handler)

    return foundHandlers


def initLogging(configFileName: str = None, streamLogLevel: str = None) -> None:
    """ Configures logging given a (JSON) config file name.

        If configFileName is None, the default logging (from iriscc/lib/default_logging.yaml) is
        used.

        Args:
            configFileName: JSON file with log config.
            streamLogLevel:
                If given it overrides the log level of StreamHandlers in the config.
                All messages below this level will be suppressed.
    """
    if configFileName is None:
        configFileName = os.path.join(THIS_MODULE_DIR, "default_logging.json")

    with open(configFileName, 'r') as stream:
        lines = stream.readlines()
        cfgLines = ''.join(lines)

    # Ensure the directory exists if @logDir@ is in the JSON file.
    logDir = argosLogDirectory()
    if '@logDir@' in cfgLines:
        ensureDirectoryExists(logDir)

    configDict = json.loads(cfgLines)
    configDict = replaceStringsInDict(configDict, "@logDir@", logDir)

    logging.config.dictConfig(configDict)

    if streamLogLevel:
        # Using getLevelName to get the level number. This undocumented behavior has been upgraded
        # to documented behavior in Python 3.4.2.
        # See https://docs.python.org/3.4/library/logging.html#logging.getLevelName
        levelNr = logging.getLevelName(streamLogLevel.upper()) - 1
        #logging.disable(levelNr)

        for streamHandler in findStreamHandlersInConfig():
            logger.debug("Setting log level to {} in handler: {} ".format(levelNr, streamHandler))
            streamHandler.setLevel(levelNr)

    logging.info("Initialized logging from: '{}'".format(normRealPath(configFileName)))
    logging.info("Default location of log files: '{}'".format(logDir))


def logDictionary(dictionary: Dict[Any, Any],
                  msg: str = '',
                  logger: logging.Logger = None,
                  level: Union[str, int] = 'debug',
                  itemPrefix: str = '    ') -> None:
    """ Writes a log message with key and value for each item in the dictionary.

        Args:
            dictionary: The dictionary to be logged.
            msg: An optional message that is logged before the contents.
            logger: A logging.Logger object to log to. If not set, the 'main' logger is used.
            level: The log level. String or int as described in the logging module documentation.
                Default: 'debug'.
            itemPrefix: String that will be prefixed to each line.
                Default: four spaces.
    """
    if isinstance(level, str):
        level = level.upper()

    levelNr = logging.getLevelName(level)

    if logger is None:
        logger = logging.getLogger('main')

    if msg :
        logger.log(levelNr, "Logging dictionary: {}".format(msg))

    if not dictionary:
        logger.log(levelNr,"{}<empty dictionary>".format(itemPrefix))
        return

    maxKeyLen = max([len(k) for k in dictionary.keys()])

    for key, value in sorted(dictionary.items()):
        logger.log(levelNr, "{0}{1:<{2}s} = {3}".format(itemPrefix, key, maxKeyLen, value))


def makeLogFormat(
        ascTime: bool = True,
        processId: bool = False,
        threadName: bool = False,
        threadId: bool = False,
        fileLine: bool = True,
        loggerName: bool = False,
        level: bool = True) -> str:
    """ Creates a format string that can be used in logging.basicConfig.

        Example: ::

            logging.basicConfig(level="DEBUG", format=makeLogFormat(fileLine=False))
    """
    parts = []
    if ascTime:
        parts.append('%(asctime)s')

    if processId:
        parts.append('pid=%(process)5d')

    if threadName:
        parts.append('%(threadName)15s')

    if threadId:
        parts.append('id=0x%(thread)x')

    if fileLine:
        parts.append('%(filename)25s:%(lineno)-4d')

    if loggerName:
        parts.append("%(name)30s")

    if level:
        parts.append('%(levelname)-7s')

    parts.append('%(message)s')
    return " : ".join(parts)
