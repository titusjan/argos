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

r""" Various functions related to logging
"""
import logging
import logging.config
import os.path
import json

from argos.utils.dirs import ensureDirectoryExists, normRealPath, argosLogDirectory
from argos.utils.misc import replaceStringsInDict

logger = logging.getLogger(__name__)


THIS_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))

#
# DEFAULT_LOG_CFG = {
#     'formatters': {
#         'fileFormatter': {
#             'format': '%(asctime)s.%(msecs)03d : pid = %(process)5d : %(threadName)-13s tid = %(thread)5d : %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s',
#             'datefmt': '%Y-%m-%d %H:%M:%S'
#         },
#         'screenFormatter': {
#             'format': '%(asctime)s.%(msecs)03d : pid = %(process)5d : %(threadName)-13s tid = %(thread)5d : %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s',
#             'datefmt': '%Y-%m-%d %H:%M:%S'
#         }
#     },
#
#     'handlers': {
#         'streamHandler': {
#             'class': 'logging.handlers.StreamHandler',
#             'formatter': 'screenFormatter',
#             'stream': 'ext://sys.stderr',
#             'level': 'DEBUG',
#         },
#
#         # The handler that writes to the (operational log file).
#         # This is the log file that is shown when the user clicks the 'show log' file button in the exception dialog.
#         # Therefore do not rename this handler.
#         'currentRunHandler': {
#             'class': 'logging.handlers.FileHandler',
#             'formatter': 'fileFormatter',
#             'filename': '@logDir@/last_run.log',
#             'encoding': 'utf-8',
#             'delay': 'true',  # only create file when used.
#             'mode': 'w',
#             'level': 'DEBUG',
#         },
#
#         'rotatingFileHandler': {  #
#             'class': 'logging.handlers.TimedRotatingFileHandler',
#             'formatter': 'fileFormatter',
#             'filename': '@logDir@/argos.log',
#             'backupCount': 5,
#             'when': 'd',
#             'interval': '1',
#             'encoding': 'utf-8',
#             'delay': 'true',   # only create file when used.
#             'mode': 'a',
#             'level': 'DEBUG',
#         }
#     },
#
#     # This sets level of all log messages, including messages from 3rd party libraries.
#     # In the loggers section below you can override the log levels of (sub)components.
#     'root' : {
#         'level': 'WARNING',
#         'handlers': ['streamHandler', 'currentRunHandler', 'rotatingFileHandler'],
#     },
#
#     'loggers': {
#         'argos': {
#             'level': 'DEBUG',
#         }
#     }
# }

def findStreamHandlersInConfig():
    """ Searches for a handlers with 'stream' their name. Returns a list of handlers.
    """
    rootLogger = logging.getLogger()
    #logger.debug("Searching for Handlers in the root logger haveing 'stream' in their name")
    foundHandlers = []
    for handler in rootLogger.handlers:
        #logger.debug("  handler name: {}".format(handler.name))
        if 'stream' in handler.name.lower():
            foundHandlers.append(handler)

    return foundHandlers



def initLogging(configFileName=None, streamLogLevel=None):
    """ Configures logging given a (JSON) config file name.

        If configFileName is None, the default logging (from iriscc/lib/default_logging.yaml) is
        used.

        :param configFileName: JSON file with log config.
        :param streamLogLevel: If given it overrides the log level of StreamHandlers in the config. All messages below
            this level will be suppressed.
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


def log_dictionary(dictionary, msg='', logger=None, level='debug', item_prefix='    '):
    """ Writes a log message with key and value for each item in the dictionary.

        :param dictionary: the dictionary to be logged
        :type dictionary: dict
        :param name: An optional message that is logged before the contents
        :type name: string
        :param logger: A logging.Logger object to log to. If not set, the 'main' logger is used.
        :type logger: logging.Logger or a string
        :param level: log level. String or int as described in the logging module documentation.
            Default: 'debug'.
        :type level: string or int
        :param item_prefix: String that will be prefixed to each line. Default: two spaces.
        :type item_prefix: string
    """
    level_nr = logging.getLevelName(level.upper())

    if logger is None:
        logger = logging.getLogger('main')

    if msg :
        logger.log(level_nr, "Logging dictionary: {}".format(msg))

    if not dictionary:
        logger.log(level_nr,"{}<empty dictionary>".format(item_prefix))
        return

    max_key_len = max([len(k) for k in dictionary.keys()])

    for key, value in sorted(dictionary.items()):
        logger.log(level_nr, "{0}{1:<{2}s} = {3}".format(item_prefix, key, max_key_len, value))


def make_log_format(
        ascTime = True,
        processId = False,
        threadName = False,
        threadId = False,
        fileLine = True,
        loggerName = False,
        level = True):
    """ Creates a format string to use in logging.basicConfig.

        Use example:
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
