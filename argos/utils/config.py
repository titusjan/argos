# -*- coding: utf-8 -*-

""" Various function related to config files.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

ConfigDict = Dict[str, Any]

def __findConfigParameter(cfg, parts, orgPath):
    """ Recursively finds a parameter in a (config) dict.
    """
    if len(parts) == 0:
        return cfg  # Trailing slash

    head, tail = parts[0], parts[1:]

    if head == "":  # A leading slash or double orgPath
        return __findConfigParameter(cfg, tail, orgPath)

    if head not in cfg:
        msg = "Path {!r} not found in dict. {!r} not in: {}".format(orgPath, head, list(cfg.keys()))
        raise KeyError(msg)

    if len(tail) == 0:
        return cfg[head]
    else:
        return __findConfigParameter(cfg[head], tail, orgPath)


def findConfigParameter(cfg, path):
    """ Recursively finds a parameter in a config dict.

        Raises KeyError if the path cannot be found.

        :param cfg: config dictionary. Can be a recursive dict (a dict of dicts, etc)
        :param path: Slash separated parameter path. E.g.: '/dict1/dict2/parameter'
    """
    if not path:
        # An empty path is most likely a programming error
        raise KeyError("Empty path given to findConfigParameter: {}".format(path))
    else:
        parts = path.split('/')
        return __findConfigParameter(cfg, parts, path)


def getConfigParameter(cfg, path, alt=None):
    """ Finds the findConfigParameter. Returns alternative value if not found.

        Will still log a warning if the parameter is not found.

        :param cfg: config dictionary. Can be a recursive dict (a dict of dicts, etc)
        :param path: Slash separated parameter path. E.g.: '/dict1/dict2/parameter'
    """
    try:
        return findConfigParameter(cfg, path)
    except KeyError:
        logger.warning("Could not find path in config: {!r}".format(path))
        return alt



def deleteParameter(cfg, parentPath, parName):
    """ Deletes a parameter from the config dict

        :param cfg: config dictionary
        :param parentPath: the path of the parent dict that contains the paremeter
        :param parName: name of the element that will be removed
    """
    logger.debug("Deleting {!r} from parent dict: {!r}".format(parName, parentPath))
    try:
        parentCfg = findConfigParameter(cfg, parentPath)
    except KeyError:
        logger.warning("Could not find path in configur: {!r}".format(parentPath))
        return

    try:
        del parentCfg[parName]
    except KeyError:
        logger.warning("Could not find {!r} in parent dict: {!r}".format(parName, parentPath))
        return
    except Exception as ex:
        # The element might not be a dict
        logger.warning("Error while deleting {!r} from parent dict {!r}: {}"
                       .format(parName, parentPath, ex))
        return
