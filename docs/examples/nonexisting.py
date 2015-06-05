""" Tries to install a non-existing RTI plugin
"""

import sys

# Uncomment the next line to run the example from within the distribution
# sys.path.append("../../")

import libargos
from libargos.application import ArgosApplication
 
def main():
    argosApp = ArgosApplication()
    if '--reset-registry' in sys.argv:
        argosApp.rtiRegistry.deleteSettings()
    argosApp.loadOrInitRegistries()
    argosApp.rtiRegistry.registerRti('SVG File', 'titusjan.svg.SvgFile', extensions=['.svg'])
    argosApp.rtiRegistry.saveSettings()
    
if __name__ == "__main__":
    libargos.configBasicLogging(level='DEBUG')
    main()

