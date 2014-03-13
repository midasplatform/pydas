#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# Library:   pydas
#
# Copyright 2010 Kitware Inc. 28 Corporate Drive,
# Clifton Park, NY, 12065, USA.
#
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 ( the "License" );
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################

"""Module for the main user classes for pydas.
"""
import pydas.drivers
import pydas.exceptions


class Communicator(object):
    """Class for communicating with the Midas server through its drivers.
    """

    def __init__(self, url, drivers=None):
        """Constructor that takes a Midas url and an optional list of drivers
        to use
        """
        if drivers is None:
            self._drivers = []
            import inspect

            base_driver_class = pydas.drivers.BaseDriver
            for name, obj in inspect.getmembers(pydas.drivers):
                if inspect.isclass(obj):
                    class_hierarchy = inspect.getmro(obj)
                    if base_driver_class in class_hierarchy and obj != base_driver_class:
                        instance = obj(url)
                        self._drivers.append(instance)
        else:
            self._drivers = drivers
        self._url = url

    def __getattr__(self, name):
        """Called when a function does not exist in the class. We pass it down
        to one of the registered drivers.
        """
        for driver in self.drivers:
            if hasattr(driver, name):
                return getattr(driver, name)
        raise AttributeError("%r object has no attribute %r" %
                             (type(self).__name__, name))

    @property
    def drivers(self):
        """Get the list of drivers
        """
        return self._drivers

    @property
    def url(self):
        """Getter for the url.
        """
        if len(self.drivers) > 0:
            return self.drivers[0].url
        else:
            return self._url

    @url.setter
    def url(self, value):
        """Setter for the url.
        """
        for driver in self.drivers:
            driver.url = value

    @property
    def debug(self):
        """Return the debug state of all drivers by logically anding them.
        """
        return all(driver.debug for driver in self.drivers)

    @debug.setter
    def debug_set(self, value):
        """Set the debug state on all of the drivers attached to the
        communicator.
        """
        for driver in self.drivers:
            driver.debug = value

    def set_auth(self, value):
        for driver in self.drivers:
            driver.auth = value
