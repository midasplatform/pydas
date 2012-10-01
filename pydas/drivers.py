#!/usr/bin/evn python
# -*- coding: utf-8 -*-

################################################################################
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
################################################################################

"""This module is for the drivers that actually do the work of communication with
the Midas server. Any drivers that are implemented should use the utility
functions provided in pydas.drivers.BaseDriver by inheriting from that class.
"""

import json
import requests as http
import os
import StringIO as sio
from pydas.exceptions import PydasException
import pydas.retry as retry


class BaseDriver(object):
    """Base class for the Midas api drivers.
    """

    # Class members.
    email = ''
    apikey = ''

    def __init__(self, url=""):
        """Constructor
        """
        self._api_suffix = '/api/json?method='
        self._url = url
        self._debug = False

    @property
    def url(self):
        """Getter for the url
        """
        return self._url

    @url.setter
    def url_set(self, value):
        """Set the url
        """
        self._url = value

    @property
    def full_url(self):
        """Return the full path the the url (including the api extensions).
        """
        return self._url + self._api_suffix

    @property
    def debug(self):
        """Return the debug state of the driver
        """
        return self._debug

    @debug.setter
    def debug_set(self, value):
        """Setter for debug state

        :param value: The value to set the debug state
        """
        self._debug = value

    @retry.reauth
    def request(self, method, parameters=None, file_payload=None):
        """Do the generic processing of a request to the server.

        If file_payload is specified, it will be PUT to the server.

        :param method: String to be passed to the server indicating the desired method.
        :param parameters: (optional) Dictionary to pass in the HTTP body.
        :param file_payload: (optional) File-like object to be sent with the HTTP request
        :returns: Dictionary representing the json response to the request.
        """
        method_url = self.full_url + method
        request = None
        if file_payload:
            request = http.put(method_url,
                               data=file_payload.read(),
                               params=parameters,
                               allow_redirects=True,
                               verify=False)
        else:
            request = http.post(method_url,
                                params=parameters,
                                allow_redirects=True,
                                verify=False)
        code = request.status_code
        if self._debug:
            print request.content
        if code != 200 and code != 302:
            raise PydasException("Request failed with HTTP error code "
                                 "%d" % code)
        try:
            response = json.loads(request.content)
        except json.JSONDecodeError:
            raise PydasException("Request failed with HTTP error code "
                                 "%d and request.content %s" % (code, request.content))

        if response['stat'] != 'ok':
            exception = PydasException("Request failed with Midas error code "
                                 "%s: %s" % (response['code'],
                                             response['message']))
            exception.code = response['code']
            exception.method = method
            raise exception
        return response['data']

    def login_with_api_key(self, cur_email, cur_apikey, application='Default'):
        """Login and get a token.

        If you do not specify a specific application, 'Default' will be used.

        :param cur_email: The email of the user.
        :param cur_apikey: A valid api-key assigned to the user.
        :param application: (optional) Application designated for this api key.
        :returns: String of the token to be used for interaction with the api until expiration.
        """
        parameters = dict()
        parameters['email'] = BaseDriver.email = cur_email     # Cache email
        parameters['apikey'] = BaseDriver.apikey = cur_apikey  # Cache api key
        parameters['appname'] = application
        response = self.request('midas.login', parameters)
        if 'token' in response:  # normal case
            return response['token']
        if 'mfa_token_id':       # case with multi-factor authentication
            return response['mfa_token_id']


class CoreDriver(BaseDriver):
    """Driver for the core API methods of Midas.

    This contains all of the calls necessary to interact with a Midas instance
    that has no plugins enabled (other than the web-api).
    """

    def get_server_version(self):
        """Get the version from the server.

        :returns: String version code from the server.
        """
        response = self.request('midas.version')
        return response['version']

    def get_server_info(self):
        """Get general server information.

        The information provided includes enabled modules as well as enabled
        web api functions.

        :returns: Dictionary of dictionaries containing module and web-api information.
        """
        response = self.request('midas.info')
        return response['version']

    def list_user_folders(self, token):
        """List the folders in the users home area.

        :param token: A valid token for the user in question.
        :returns: List of dictionaries containing folder information.
        """
        parameters = dict()
        parameters['token'] = token
        response = self.request('midas.user.folders', parameters)
        return response

    def get_default_api_key(self, email, password):
        """Get the default api key for a user.

        :param email: The email of the user.
        :param password: The user's password.
        :returns: String api-key to confirm that it was fetched successfully.
        """
        parameters = dict()
        parameters['email'] = email
        parameters['password'] = password
        response = self.request('midas.user.apikey.default', parameters)
        return response['apikey']

    def list_users(self, limit=20):
        """List the public users in the system.

        :param limit: The number of users to fetch.
        :returns: The list of users.
        """
        parameters = dict()
        parameters['limit'] = limit
        response = self.request('midas.user.list', parameters)
        return response

    def get_user_by_name(self, firstname, lastname):
        """Get a user by the first and last name of that user.

        :param firstname: The first name of the user.
        :param lastname: The last name of the user.
        :returns: The user requested.
        """
        parameters = dict()
        parameters['firstname'] = firstname
        parameters['lastname'] = lastname
        response = self.request('midas.user.get', parameters)
        return response

    def get_user_by_id(self, user_id):
        """Get a user by the first and last name of that user.

        :param user_id: The id of the desired user.
        :returns: The user requested.
        """
        parameters = dict()
        parameters['user_id'] = user_id
        response = self.request('midas.user.get', parameters)
        return response

    def get_user_by_email(self, email):
        """Get a user by the email of that user.

        :param email: The email of the desired user.
        :returns: The user requested.
        """
        parameters = dict()
        parameters['email'] = email
        response = self.request('midas.user.get', parameters)
        return response

    def get_community_by_name(self, name, token=None):
        """Get a community based on its name.

        :param name: The name of the target community.
        :param token: (optional) A valid token for the user in question.
        :returns: The requested community.
        """
        parameters = dict()
        parameters['name'] = name
        if token:
            parameters['token'] = token
        response = self.request('midas.community.get', parameters)
        return response

    def get_community_by_id(self, community_id, token=None):
        """Get a community based on its id.

        :param community_id: The id of the target community.
        :param token: (optional) A valid token for the user in question.
        :returns: The requested community.
        """
        parameters = dict()
        parameters['id'] = community_id
        if token:
            parameters['token'] = token
        response = self.request('midas.community.get', parameters)
        return response

    def create_folder(self, token, name, parent, **kwargs):
        """Create a folder at the destination specified.

        :param token: A valid token for the user in question.
        :param name: The name of the folder to be created.
        :param parent: The id of the targeted parent folder.
        :param description: (optional) The description text of the folder.
        :param uuid: (optional) The UUID for the folder. It will be generated if not given.
        :param privacy: (optional) The privacy state of the folder ('Public' or 'Private').
        :returns: Dictionary containing the details of the created folder.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parent
        parameters['description'] = ''
        optional_keys = ['description', 'uuid', 'privacy']
        for key in optional_keys:
            if key in kwargs:
                parameters[key] = kwargs[key]
        response = self.request('midas.folder.create', parameters)
        return response

    def folder_get(self, token, folder_id):
        """Get the attributes of the specified folder.

        :param token: A valid token for the user in question.
        :param folder_id: The id of the requested folder.
        :returns: Dictionary of the folder attributes.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = folder_id
        response = self.request('midas.folder.get', parameters)
        return response

    def folder_children(self, token, folder_id):
        """Get the non-recursive children of the passed in folder_id.

        :param token: A valid token for the user in question.
        :param folder_id: The id of the requested folder.
        :returns: Dictionary of two lists: 'folders' and 'items'.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = folder_id
        response = self.request('midas.folder.children', parameters)
        return response

    def delete_folder(self, token, folder_id):
        """Delete the folder with the passed in folder_id.

        :param token: A valid token for the user in question.
        :param folder_id: The id of the folder to be deleted.
        :returns: None.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = folder_id
        response = self.request('midas.folder.delete', parameters)
        return response

    def move_folder(self, token, item_id, dest_folder_id):
        """Move a folder to the desination folder.

        :param token: A valid token for the user in question.
        :param folder_id: The id of the folder to be moved.
        :param dest_folder_id: The id of destination (new parent) folder.
        :returns: Dictionary containing the details of the moved folder.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        parameters['dstfolderid'] = dest_folder_id
        response = self.request('midas.folder.move', parameters)
        return response

    def create_item(self, token, name, parentid, **kwargs):
        """Create an item to the server.

        :param token: A valid token for the user in question.
        :param name: The name of the item to be created.
        :param parentid: The id of the destination folder.
        :param description: (optional) The description text of the item.
        :param uuid: (optional) The UUID for the item. It will be generated if not given.
        :param privacy: (optional) The privacy state of the item ('Public' or 'Private').
        :returns: Dictionary containing the details of the created item.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parentid
        parameters['privacy'] = 'Public'
        optional_keys = ['description', 'uuid', 'privacy']
        for key in optional_keys:
            if key in kwargs:
                parameters[key] = kwargs[key]
        response = self.request('midas.item.create', parameters)
        return response

    def item_get(self, token, item_id):
        """Get the attributes of the specified item.

        :param token: A valid token for the user in question.
        :param item_id: The id of the requested item.
        :returns: Dictionary of the item attributes.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        response = self.request('midas.item.get', parameters)
        return response

    def download_item(self, item_id, token=None, revision=None):
        """Download an item to disk.

        :param item_id: The id of the item to be downloaded.
        :param token: (optional) The authentication token of the user requesting the download.
        :param revision: (optional) The revision of the item to download, This defaults to HEAD.
        :returns: A tuple of the filename and the content iterator.
        """
        parameters = dict()
        parameters['id'] = item_id
        if token:
            parameters['token'] = token
        if revision:
            parameters['revision'] = revision
        method_url = self.full_url + 'midas.item.download'
        request = http.get(method_url,
                           params=parameters,
                           verify=False)
        filename = request.headers['content-disposition'][21:].strip('"')
        return (filename, request.iter_content())

    def delete_item(self, token, item_id):
        """Delete the item with the passed in item_id.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item to be deleted.
        :returns: None.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        response = self.request('midas.item.delete', parameters)
        return response

    def get_item_metadata(self, item, token=None, revision=None):
        """Get the metadata associated with an item.

        :param item_id: The id of the item for which metadata will be returned
        :param token: (optional) A valid token for the user in question.
        :param revision: (optional) Revision of the item. Defaults to latest revision.
        :returns: List of dictionaries containing item metadata.
        """
        parameters = dict()
        parameters['id'] = item
        if token:
            parameters['token'] = token
        if revision:
            parameters['revision'] = revision
        response = self.request('midas.item.getmetadata', parameters)
        return response

    def set_item_metadata(self, token, item_id, element, value, qualifier=None):
        """Set the metadata associated with an item.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item for which metadata will be set.
        :param element: The metadata element name.
        :param value: The metadata value for the field.
        :param qualifier: (optional) The metadata qualifier. Defaults to empty string.
        :returns: None.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemId'] = item_id
        parameters['element'] = element
        parameters['value'] = value
        if qualifier:
            parameters['qualifier'] = qualifier
        response = self.request('midas.item.setmetadata', parameters)
        return response

    def share_item(self, token, item_id, dest_folder_id):
        """Share an item to the destination folder.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item to be shared.
        :param dest_folder_id: The id of destination folder where the item is shared to.
        :returns: Dictionary containing the details of the shared item.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        parameters['dstfolderid'] = dest_folder_id
        response = self.request('midas.item.share', parameters)
        return response

    def move_item(self, token, item_id, src_folder_id, dest_folder_id):
        """Move an item from the source folder to the desination folder.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item to be moved.
        :param src_folder_id: The id of source folder where the item is located.
        :param dest_folder_id: The id of destination folder where the item is moved to.
        :returns: Dictionary containing the details of the moved item.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        parameters['srcfolderid'] = src_folder_id
        parameters['dstfolderid'] = dest_folder_id
        response = self.request('midas.item.move', parameters)
        return response

    def generate_upload_token(self, token, item_id, filename, checksum=None):
        """Generate a token to use for upload.

        Midas uses a individual token for each upload. The token corresponds to
        the file specified and that file only. Passing the MD5 checksum allows
        the server to determine if the file is already in the assetstore.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item in which to upload the file as a bitstream.
        :param filename: The name of the file to generate the upload token for.
        :param checksum: (optional) The checksum of the file to upload.
        :returns: String of the upload token.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemid'] = item_id
        parameters['filename'] = filename
        if not checksum == None:
            parameters['checksum'] = checksum
        response = self.request('midas.upload.generatetoken', parameters)
        return response['token']

    def perform_upload(self, uploadtoken, filename, **kwargs):
        """Upload a file into a given item (or just to the public folder if the
        item is not specified.

        :param uploadtoken: The upload token (returned by generate_upload_token)
        :param filename: The upload filename. Also used as the path to the file, if 'filepath' is not set.
        :param mode: (optional) Stream or multipart. Default is stream.
        :param folderid: (optional) The id of the folder to upload into.
        :param item_id: (optional) If set, will create a new revision in the existing item.
        :param revision: (optional) If set, will add a new file into an existing revision. Set this to "head" to add to the most recent revision.
        :param filepath: (optional) The path to the file.
        :returns: Dictionary containing the details of the item created or changed.
        """
        parameters = dict()
        parameters['uploadtoken'] = uploadtoken
        parameters['filename'] = filename
        parameters['revision'] = 'head'

        optional_keys = ['mode', 'folderid', 'item_id', 'itemid', 'revision']
        for key in optional_keys:
            if key in kwargs:
                if key == 'item_id':
                    parameters['itemid'] = kwargs[key]
                    continue
                parameters[key] = kwargs[key]

        # We may want a different name than path
        file_payload = open(kwargs.get('filepath', filename), 'rb')
        # Arcane getting of the file size using fstat. More details can be
        # found in the python library docs
        parameters['length'] = os.fstat(file_payload.fileno()).st_size

        response = self.request('midas.upload.perform', parameters,
                                file_payload)
        return response

    def search(self, search, token=None):
        """Get the resources corresponding to a given query.

        :param search: The search criterion.
        :param token: (optional) The credentials to use when searching.
        :returns: Dictionary containing the search result. Notable is the dictionary item 'results', which is a list of item details.
        """
        parameters = dict()
        parameters['search'] = search
        if token:
            parameters['token'] = token
        response = self.request('midas.resource.search', parameters)
        return response


class BatchmakeDriver(BaseDriver):
    """Driver for the Midas batchmake module's API methods.
    """

    def add_condor_dag(self, token, batchmaketaskid, dagfilename, dagmanoutfilename):
        """Adds a condor dag to the given batchmake task
        """
        parameters = dict()
        parameters['token'] = token
        parameters['batchmaketaskid'] = batchmaketaskid
        parameters['dagfilename'] = dagfilename
        parameters['outfilename'] = dagmanoutfilename
        response = self.request('midas.batchmake.add.condor.dag', parameters)
        return response

    def add_condor_job(self, token, batchmaketaskid, jobdefinitionfilename, outputfilename, errorfilename, logfilename, postfilename):
        """Adds a condor dag job to the condor dag associated with this batchmake task
        """
        parameters = dict()
        parameters['token'] = token
        parameters['batchmaketaskid'] = batchmaketaskid
        parameters['jobdefinitionfilename'] = jobdefinitionfilename
        parameters['outputfilename'] = outputfilename
        parameters['errorfilename'] = errorfilename
        parameters['logfilename'] = logfilename
        parameters['postfilename'] = postfilename
        response = self.request('midas.batchmake.add.condor.job', parameters)
        return response


class DicomextractorDriver(BaseDriver):
    """Driver for the Midas dicomextractor module's API methods.
    """

    def extract_dicommetadata(self, token, item_id):
        """Extracts DICOM metadata from the given item
        """
        parameters = dict()
        parameters['token'] = token
        parameters['item'] = item_id
        response = self.request('midas.dicomextractor.extract', parameters)
        return response


class MultiFactorAuthenticationDriver(BaseDriver):
    """Driver for the multi-factor authentication module's API methods.
    """

    def mfa_otp_login(self, temp_token, one_time_pass):
        """ Log in to get the real token using the temporary token and otp.

        :param temp_token: The temporary token (or id) returned from normal login
        :param one_time_pass: The one-time pass to be sent to the underlying multi-factor engine.
        :returns: A standard token for interacting with the web api.
        """
        parameters = dict()
        parameters['mfaTokenId'] = temp_token
        parameters['otp'] = one_time_pass
        response = self.request('midas.mfa.otp.login', parameters)
        return response['token']
