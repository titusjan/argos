""" Tries to install a non-existing RTI plugin
"""
import sys

# Uncomment the next line to run the example from within the distribution
# sys.path.append("../../")

import libargos, logging
from libargos.repo.registry import RtiRegistry

logger = logging.getLogger('libargos')
 
def main():
    rtiRegistry = RtiRegistry()
    if '--reset-registry' in sys.argv:
        rtiRegistry.deleteSettings()
    rtiRegistry.loadOrInitSettings()
    
    rtiRegistry.registerRti('SVG File', 'titusjan.svg.SvgFile', extensions=['.svg'])
    rtiRegistry.saveSettings()
    
if __name__ == "__main__":
    libargos.configBasicLogging(level='DEBUG')
    main()
    logger.info("Done...")

