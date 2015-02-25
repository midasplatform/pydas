#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# Library: pydas
#
# Copyright 2010 Kitware, Inc., 28 Corporate Dr., Clifton Park, NY 12065, USA.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""Module for the main user classes for pydas."""

import pydas.drivers
import pydas.exceptions


class Communicator(object):
    """Class for communicating with Midas Server through its drivers."""

    def __init__(self, url, drivers=None):
        """
        Constructor. Takes the URL of the Midas Server instance and an optional
        list of drivers to use.

        :param url: URL of the server
        :type url: string
        :param drivers: (optional) list of drivers to be attached to this
            communicator
        :type drivers: None | list [T <= pydas.drivers.BaseDriver]
        """
        if drivers is None:
            self._drivers = []
            import inspect

            base_driver_class = pydas.drivers.BaseDriver
            for name, obj in inspect.getmembers(pydas.drivers):
                if inspect.isclass(obj):
                    class_hierarchy = inspect.getmro(obj)
                    if base_driver_class in class_hierarchy and \
                            obj != base_driver_class:
                        instance = obj(url)
                        self._drivers.append(instance)
        else:
            self._drivers = drivers
        self._url = url

    def __getattr__(self, name):
        """
        Called when a function does not exist in the class. Pass the call down
        to one of the registered drivers.

        :raises AttributeError: if there is no function with the given name in
            any of the drivers
        """
        for driver in self.drivers:
            if hasattr(driver, name):
                return getattr(driver, name)
        raise AttributeError('{0} object has no attribute {1}'
                             .format(type(self).__name__, name))

    @property
    def drivers(self):
        """
        Get the list of drivers attached to this communicator.

        :returns: list of drivers
        :rtype: list[T <= pydas.drivers.BaseDriver]
        """
        return self._drivers

    @property
    def url(self):
        """
        Return the URL of the server.

        :returns: URL of the server
        :rtype: string
        """
        if len(self.drivers) > 0:
            return self.drivers[0].url
        else:
            return self._url

    @url.setter
    def url(self, value):
        """
        Set the URL of the server in all drivers attached to this communicator.

        :param value: URL of the server
        :type value: string
        """
        for driver in self.drivers:
            driver.url = value

    @property
    def debug(self):
        """
        Return whether the debug state of every driver is True.

        :returns: True if the debug state of every driver is True
        :rtype: bool
        """
        return all(driver.debug for driver in self.drivers)

    @debug.setter
    def debug(self, value):
        """
        Set the debug state of all of drivers attached to this communicator.

        :param value: debug state of all drivers
        :type value: bool
        """
        for driver in self.drivers:
            driver.debug = value

    @property
    def verify_ssl_certificate(self):
        """
        Return whether the SSL certificate will be verified for all drivers
        attached to this communicator.

        :returns: True if the SSL certificate will be verified for every driver
        :rtype: bool
        """
        return all(driver.verify_ssl_certificate for driver in self.drivers)

    @verify_ssl_certificate.setter
    def verify_ssl_certificate(self, value):
        """
        Set whether the SSL certificate will be verified.

        :param value: If True, the SSL certificate will be verified
        :type value: bool
        """
        for driver in self.drivers:
            driver.verify_ssl_certificate = value

    def set_auth(self, value):
        """
        Set the authentication in all drivers attached to this communicator.

        :param value: authentication tuple to be passed to requests.request()
        :type value: None | tuple
        """
        for driver in self.drivers:
            driver.auth = value
