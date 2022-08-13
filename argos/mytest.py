""" Small test program to check documentation in sphinx
"""
from typing import List

from argos.repo.baserti import BaseRti

        # Args:
        #     rtis: candidates

def bestRti(rtis: List[BaseRti], fna: float) -> BaseRti:
    """ Test function to see how parameters are documented

        Selects the best RTI in the whole of Utoxeter.

        Args:
            rtis:
                The list of candidates
            fna: specifies a fnaggel to assist in the search

        Returns:
             The best we've found
    """
    pass

