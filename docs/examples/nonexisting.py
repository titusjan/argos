""" Tries to install a non-existing RTI plugin
"""
import sys

# Uncomment the next line to run the example from within the distribution.
# sys.path.append("../../")

import os, logging
import argos
from argos.qt import initQApplication
from argos.repo.registry import RtiRegistry
from argos.inspector.registry import InspectorRegistry

logger = logging.getLogger('argos')

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))



def registerRtis():

    registry = RtiRegistry()
    if '--reset-registry' in sys.argv:
        registry.deleteSettings()
    registry.loadOrInitSettings()


    registry.registerRti('Python File', 'example_plugin.TestFileRti', extensions=['.py'],
                         pythonPath=SCRIPT_DIR)
    registry.registerRti('SVG File', 'does_not_exist.svg.SvgFile', extensions=['.svg'])
    registry.saveSettings()


def registerInspectors():

    registry = InspectorRegistry()
    if '--reset-registry' in sys.argv:
        registry.deleteSettings()
    registry.loadOrInitSettings()

    registry.registerInspector('Non Existing', 'does_not_exist.Inspector')
    registry.saveSettings()


def main():
    logger.info("Start...")
    logger.debug("current dir: {}".format(SCRIPT_DIR))

    # Important: instantiate a Qt application first to use the correct settings file/winreg.
    _app = initQApplication()

    registerRtis()
    registerInspectors()
    logger.info("Done...")


if __name__ == "__main__":
    argos.configBasicLogging(level='DEBUG')
    main()


