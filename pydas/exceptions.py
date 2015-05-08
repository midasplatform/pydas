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

"""Module for exceptions in pydas."""

import requests.exceptions


class PydasException(Exception):
    """Base class for exceptions defined in pydas."""

    def __init__(self, value):
        """
        Override the constructor to support a basic message.

        :param value: Message to display.
        :type value: string
        """
        super(PydasException, self).__init__()
        self.value = value
        self.method = None
        self.code = None

    def __str__(self):
        """
        Override the string method.

        :returns: String representation of the message.
        :rtype: string
        """
        return repr(self.value)


class RequestError(PydasException, requests.exceptions.ConnectionError):
    """Error relating to an HTTP request."""

    def __init__(self, value, request=None):
        """
        Override the constructor to store the request sent.

        :param value: Message to display.
        :type value: string
        :param request: (optional) Request sent.
        :type request: requests.Request
        """
        super(RequestError, self).__init__(value)
        self.request = request


class SSLVerificationFailed(RequestError, requests.exceptions.SSLError):
    """Error verifying an SSL certificate."""


class ResponseError(PydasException):
    """Error relating to an HTTP response."""

    def __init__(self, value, response=None):
        """
        Override the constructor to store the response received.

        :param value: Message to display.
        :type value: string
        :param response: (optional) Response received.
        :type response: requests.Response
        """
        super(ResponseError, self).__init__(value)
        self.response = response


class ParseError(ResponseError, ValueError):
    """Error parsing a response."""


class HTTPError(ResponseError, requests.exceptions.HTTPError):
    """HTTP status code 400 or above."""


class BadRequest(HTTPError):
    """HTTP status code 400: bad request."""


class InternalError(BadRequest):
    """Midas Server error code -100: internal error."""


class InvalidParameter(BadRequest, ValueError):
    """Midas Server error code -150: internal error."""


class InvalidPolicy(BadRequest, ValueError):
    """Midas Server error code  -151: invalid policy."""


class UploadFailed(BadRequest):
    """Midas Server error code -105: upload failed."""


class UploadTokenGenerationFailed(BadRequest):
    """Midas Server error code -140: upload token generation failed."""


class Unauthorized(HTTPError):
    """HTTP status code 401: unauthorized."""


class InvalidToken(Unauthorized, ValueError):
    """Midas Server error code -101: invalid token."""


class InvalidUploadToken(Unauthorized, ValueError):
    """Midas Server error code -141: invalid upload token."""


class Forbidden(HTTPError):
    """HTTP status code 403: forbidden."""


class NotFound(HTTPError):
    """HTTP status code 404: not found or HTTP status code 410: gone."""


class MethodNotAllowed(HTTPError):
    """HTTP status code 405: method not allowed."""


def get_exception_from_status_and_error_codes(status_code, error_code, value):
    """
    Return an exception given status and error codes.

    :param status_code: HTTP status code.
    :type status_code: None | int
    :param error_code: Midas Server error code.
    :type error_code: None | int
    :param value: Message to display.
    :type value: string
    :returns: Exception.
    :rtype : pydas.exceptions.ResponseError
    """
    if status_code == requests.codes.bad_request:
        exception = BadRequest(value)
    elif status_code == requests.codes.unauthorized:
        exception = Unauthorized(value)
    elif status_code == requests.codes.forbidden:
        exception = Unauthorized(value)
    elif status_code in [requests.codes.not_found, requests.codes.gone]:
        exception = NotFound(value)
    elif status_code == requests.codes.method_not_allowed:
        exception = MethodNotAllowed(value)
    elif status_code >= requests.codes.bad_request:
        exception = HTTPError(value)
    else:
        exception = ResponseError(value)

    if error_code == -100:  # MIDAS_INTERNAL_ERROR
        exception = InternalError(value)
    elif error_code == -101:  # MIDAS_INVALID_TOKEN
        exception = InvalidToken(value)
    elif error_code == -105:  # MIDAS_UPLOAD_FAILED
        exception = UploadFailed(value)
    elif error_code == -140:  # MIDAS_UPLOAD_TOKEN_GENERATION_FAILED
        exception = UploadTokenGenerationFailed(value)
    elif error_code == -141:  # MIDAS_INVALID_UPLOAD_TOKEN
        exception = InvalidUploadToken(value)
    elif error_code == -150:  # MIDAS_INVALID_PARAMETER
        exception = InvalidParameter(value)
    elif error_code == -151:  # MIDAS_INVALID_POLICY
        exception = InvalidPolicy(value)

    return exception
