"""
Modules for defining exceptions in pydas
"""

class PydasException(Exception):
    """
    Base class for exception to throw within pydas
    """

    def __init__(self, value):
        """
        Override the constructor to support a basic message
        """
        super(PydasException, self).__init__()
        self.value = value

    def __str__(self):
        """
        Override the string method
        """
        return repr(self.value)

