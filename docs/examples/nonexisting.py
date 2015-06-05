""" Tries to install a non-existing RTI plugin
"""
import sys

# Uncomment the next line to run the example from within the distribution
# sys.path.append("../../")

import os, logging
import libargos
from libargos.application import getQApplicationInstance
from libargos.repo.registry import RtiRegistry

logger = logging.getLogger('libargos')
 
def main():
    # Important: instantiate a Qt application first to use the correct settings file/winreg. 
    _app = getQApplicationInstance()
    
    rtiRegistry = RtiRegistry()
    if '--reset-registry' in sys.argv:
        rtiRegistry.deleteSettings()
    rtiRegistry.loadOrInitSettings()
    
    currentDir = os.path.dirname(os.path.realpath(__file__))
    logger.debug("current dir: {}".format(currentDir))

    rtiRegistry.registerRti('Python File', 'test_plugin.TestFileRti', extensions=['.py'],  
                             pythonPath=currentDir)
    rtiRegistry.registerRti('SVG File', 'does_not_exist.svg.SvgFile', extensions=['.svg'])
    rtiRegistry.saveSettings()
    
if __name__ == "__main__":
    libargos.configBasicLogging(level='DEBUG')
    main()
    logger.info("Done...")

