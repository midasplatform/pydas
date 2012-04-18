"""
Module for the main user classes for pydas.
"""
import pydas.drivers
import pydas.exceptions

class Communicator(object):
    """
    Class for communicating with the Midas server through its drivers.
    """

    def __init__(self, url, drivers=None):
        """
        Constructor that takes a Midas url and an optional list of drivers
        to use
        """
        if drivers is None:
            self._drivers = []
            import inspect
            baseDriverClass = pydas.drivers.BaseDriver
            for name, obj in inspect.getmembers(pydas.drivers):
                if inspect.isclass(obj):
                    classHierarchy = inspect.getmro(obj)
                    if baseDriverClass in classHierarchy and obj != baseDriverClass:
                        instance = obj(url)
                        self._drivers.append(instance)
        else:
            self._drivers = drivers
        self._url = url

    def __getattr__(self, name):
        """
        Called when a function does not exist in the class. We pass it down
        to one of the registered drivers.
        """
        for driver in self.drivers:
            if hasattr(driver, name):
                return getattr(driver, name)
        raise AttributeError("%r object has no attribute %r" %
                             (type(self).__name__, name))

    @property
    def drivers(self):
        """
        Get the list of drivers
        """
        return self._drivers

    @property
    def url(self):
        """
        Getter for the url.
        """
        if len(self.drivers) > 0:
            return self.drivers[0].url
        else:
            return self._url

    @url.setter
    def url(self, value):
        """
        Setter for the url.
        """
        for driver in self.drivers:
            driver.url = value

    @url.deleter
    def url(self):
        """
        Delete the url.
        """
        del self._url

    @property
    def debug(self):
        """Return the debug state of all drivers by logically anding them.
        """
        return all(driver.debug for driver in self.drivers)

    @debug.setter
    def debug(self, value):
        """Set the debug state on all of the drivers attached to the
        communicator.
        """
        for driver in self.drivers:
            driver.debug = value
