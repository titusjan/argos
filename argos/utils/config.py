# -*- coding: utf-8 -*-

""" Various function related to config files.
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

ConfigDict = Dict[str, Any]

def _findConfigParameter(cfg: ConfigDict, parts: List[str], orgPath: str) -> Any:
    """ Recursively finds a parameter in a (config) dict.
    """
    if len(parts) == 0:
        return cfg  # Trailing slash

    head, tail = parts[0], parts[1:]

    if head == "":  # A leading slash or double orgPath
        return _findConfigParameter(cfg, tail, orgPath)

    if head not in cfg:
        msg = "Path {!r} not found in dict. {!r} not in: {}".format(orgPath, head, list(cfg.keys()))
        raise KeyError(msg)

    if len(tail) == 0:
        return cfg[head]
    else:
        return _findConfigParameter(cfg[head], tail, orgPath)


def findConfigParameter(cfg: ConfigDict, path: str) -> Any:
    """ Recursively finds a parameter in a config dict.

        Raises:
            KeyError: if the path cannot be found.

        Args:
            cfg: config dictionary. Can be a recursive dict (a dict of dicts, etc.)
            path: Slash-separated parameter path. E.g.: '/dict1/dict2/parameter'
    """
    if not path:
        # An empty path is most likely a programming error
        raise KeyError("Empty path given to findConfigParameter: {}".format(path))
    else:
        parts = path.split('/')
        return _findConfigParameter(cfg, parts, path)


def getConfigParameter(cfg: ConfigDict, path: str, alt: Any = None) -> Any:
    """ Finds the findConfigParameter. Returns alternative value if not found.

        Will still log a warning if the parameter is not found.

        Args:
            cfg: config dictionary. Can be a recursive dict (a dict of dicts, etc.)
            path: Slash separated parameter path. E.g.: '/dict1/dict2/parameter'
            alt: Alternative value returned when the value is not found in the dictionary.
    """
    try:
        return findConfigParameter(cfg, path)
    except KeyError:
        logger.warning("Could not find path in config: {!r}".format(path))
        return alt


def deleteParameter(cfg: ConfigDict, parentPath: str, parName: str) -> None:
    """ Deletes a parameter from the config dictionary.

        Args:
            cfg: config dictionary
            parentPath: the path of the parent dict that contains the paremeter
            parName: name of the element that will be removed
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
