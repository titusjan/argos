""" Version info for this program
"""
import os

DEBUGGING = False 

VERSION = '0.1.0-devel'
REPO_NAME = "argos"
SCRIPT_NAME = "argos"
PACKAGE_NAME = "libargos"
PROJECT_NAME = "Argos"
SHORT_DESCRIPTION = ""
PROJECT_URL = "https://github.com/titusjan/argos"
AUTOR = "Pepijn Kenter"
EMAIL = "titusjan@gmail.com"
ORGANIZATION_NAME = "titusjan"
ORGANIZATION_DOMAIN = "titusjan"

def program_directory():
    """ Returns the program directory where this program is installed
    """
    return os.path.abspath(os.path.dirname(__file__))
