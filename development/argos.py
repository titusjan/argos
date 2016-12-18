#!/usr/bin/env python
""" Convenience script that starts argos in the development environment.

    Note that this is NOT the script that will be installed by setup.py. The setup.py install
    command will create and install a dedicated argos launcher script (as specified in the
    entry_points directive).
"""
import sys, os.path

# Add the parent directory to the system path so that the package can be imported.
scriptDir = os.path.dirname(os.path.realpath(__file__))
parentDir = os.path.realpath(os.path.join(scriptDir, '..'))

sys.path.insert(0, parentDir)
from argos.main import main
main()
