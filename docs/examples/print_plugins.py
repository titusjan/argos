""" Print the plutings from the registry
"""
from __future__ import print_function
import sys

# Uncomment the next line to run the example from within the distribution
# sys.path.append("../../")

import libargos
from libargos.qt import initQCoreApplication
from libargos.inspector.registry import InspectorRegistry
from libargos.repo.registry import RtiRegistry

def printReg(name, registry):
    print("{} registry....".format(name))
    for nr, regItem in enumerate(registry.items):
        print("  {0:03d}: {1.identifier:25} {1.fullClassName:30} ".format(nr, regItem))
    print()

def main():
    # Important: instantiate a Qt application first to use the correct settings file/winreg.
    _app = initQCoreApplication()

    inspectorRegistry = InspectorRegistry()
    inspectorRegistry.loadOrInitSettings()
    printReg("Inspector", inspectorRegistry)

    rtiRegistry = RtiRegistry()
    rtiRegistry.loadOrInitSettings()
    printReg("File format", rtiRegistry)


if __name__ == "__main__":
    libargos.configBasicLogging(level='WARN')
    main()

