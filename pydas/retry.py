#!/usr/bin/evn python
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

import pydas.exceptions
import pydas.session as session
import time


def reauth(fn):
    """this decorator will detect a stale token and renew the token if possible,
    then retry the failed api call.
    """
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kw):
        try:
            retVal = fn(*args, **kw)
            return retVal
        except pydas.exceptions.PydasException as detail:
            print "Caught PydasException: ", detail
            # Unable to authenticate using the given credentials.
            if 'Login failed' in detail.value:
                print('Login failed')
                raise
            elif '404' in detail.value:
                print('404 from Server')
                raise
            print "Waiting 5 seconds, then retrying request"

            # wait 30 seconds before retrying
            time.sleep(5)

            # renew the token
            # get the instance of the CoreDriver and set it as "that"
            that = args[0]
            session.token = that.login_with_api_key(that.__class__.email,
                that.__class__.apikey)
            if session.communicator is not None:
                if len(session.token) < 10:  # HACK to check for mfa being enabled
                    one_time_pass = raw_input('One-Time Password: ')
                    session.token = session.communicator.mfa_otp_login(session.token,
                        one_time_pass)
            print session.token

            # now fix up the arguments of the original call to use the renewed token
            argsList = list(args)
            argsList[2]['token'] = session.token
            args = tuple(argsList)

            # try the api call again
            retVal = fn(*args, **kw)
            return retVal
    return wrapper
