""" Small test program to check documentation in sphinx
"""
from typing import List

from argos.repo.baserti import BaseRti

        # Args:
        #     rtis: candidates


class MyClass():
    """ My class documentation
    """

    def __init__(self, rti: BaseRti):
        """ Constructor documentation

            Args:
                rti: Repo Tree Item
        """
        pass


    def yourMethod(self, a:int):
        """ Fine, do it your way then

            :param a: some parameter with a bad name.
        """



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

