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

"""Global variables to the session."""

communicator = None
email = None
api_key = None
application = None
token = None
item_upload_callbacks = []
item_download_callbacks = []
folder_download_callbacks = []
allow_existing_download_paths = False
