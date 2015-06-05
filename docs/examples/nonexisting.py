""" Tries to install a non-existing RTI plugin
"""
import sys

# Uncomment the next line to run the example from within the distribution
# sys.path.append("../../")

import libargos, logging
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
    
    rtiRegistry.registerRti('HDF File', 'libargos.repo.rtiplugins.hdf.NcdfFileRti', extensions=['.nc', '.h5'])
    rtiRegistry.registerRti('SVG File', 'titusjan.svg.SvgFile', extensions=['.svg'])
    rtiRegistry.saveSettings()
    
if __name__ == "__main__":
    libargos.configBasicLogging(level='DEBUG')
    main()
    logger.info("Done...")

