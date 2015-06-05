""" Print the plutings from the registry
"""
from __future__ import print_function
import sys

# Uncomment the next line to run the example from within the distribution
# sys.path.append("../../")

import libargos
from libargos.application import ArgosApplication
 
def printReg(name, registry):
    print("{} registry....".format(name))
    for nr, item in enumerate(registry.items):
        print("  {0:03d}: {1.identifier:20} {1.fullClassName:30} ".format(nr, item))
    print()
    
def main():
    argosApp = ArgosApplication()
    argosApp.loadOrInitRegistries()
    printReg("Inspector", argosApp.inspectorRegistry)
    printReg("File format", argosApp.rtiRegistry)

    
if __name__ == "__main__":
    libargos.configBasicLogging(level='WARN')
    main()

