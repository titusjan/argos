""" 3rd party modules and packages included in argos.
"""
import logging
import os

logger = logging.getLogger(__name__)
#
# # Set the ARGOS_CMLIB_PATH to the path of the CmLib if you want to use another version of this
# # package, for instance during development. E.g export ARGOS_CMLIB_PATH=/Users/kenter/prog/py/cmlib/
# cmLibPath = os.environ.get("ARGOS_CMLIB_PATH")
#
# if cmLibPath is not None:
#     logger.debug("Prepending to external package path: {}".format(cmLibPath))
#     __path__.insert(0, cmLibPath)


