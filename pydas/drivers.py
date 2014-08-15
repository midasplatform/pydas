#!/usr/bin/env python
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

"""This module is for the drivers that actually do the work of communication
with the Midas server. Any drivers that are implemented should use the utility
functions provided in pydas.drivers.BaseDriver by inheriting from that class.
"""

import json
import os

import requests as http

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
        self.auth = None

    @property
    def url(self):
        """Getter for the url
        """
        return self._url

    @url.setter
    def url(self, value):
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

        :param method: String to be passed to the server indicating the desired
        method.
        :param parameters: (optional) Dictionary to pass in the HTTP body.
        :param file_payload: (optional) File-like object to be sent with the
        HTTP request
        :returns: Dictionary representing the json response to the request.
        """
        method_url = self.full_url + method
        if file_payload:
            request = http.put(method_url,
                               data=file_payload.read(),
                               params=parameters,
                               allow_redirects=True,
                               verify=False,
                               auth=self.auth)
        else:
            request = http.post(method_url,
                                params=parameters,
                                allow_redirects=True,
                                verify=False,
                                auth=self.auth)
        code = request.status_code
        if self._debug:
            print request.content
        if code != 200 and code != 302:
            raise PydasException("Request failed with HTTP error code "
                                 "%d" % code)
        try:
            response = json.loads(request.content)
        except ValueError:
            raise PydasException("Request failed with HTTP error code "
                                 "%d and request.content %s" %
                                 (code, request.content))

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
        :returns: String of the token to be used for interaction with the api
        until expiration.
        """
        parameters = dict()
        parameters['email'] = BaseDriver.email = cur_email  # Cache email
        parameters['apikey'] = BaseDriver.apikey = cur_apikey  # Cache api key
        parameters['appname'] = application
        response = self.request('midas.login', parameters)
        if 'token' in response:  # normal case
            return response['token']
        if 'mfa_token_id':  # case with multi-factor authentication
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

        :returns: Dictionary of dictionaries containing module and web-api
        information.
        """
        response = self.request('midas.info')
        return response['version']

    def list_modules(self):
        """List the enabled modules on the server.

        :returns: List of names of the enabled modules.
        """
        response = self.request('midas.modules.list')
        return response['modules']

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

    def create_community(self, token, name, **kwargs):
        """Create a new community or update an existing one using the uuid.

        :param token: A valid token for the user in question.
        :param name: The community name.
        :param description: (optional) The community description.
        :param uuid: (optional) uuid of the community. If none is passed, will
        generate one.
        :param privacy: (optional) Default 'Public', possible values
        [Public|Private].
        :param can_join: (optional) Default 'Everyone', possible values
        [Everyone|Invitation].
        :returns: The community dao that was created.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        optional_keys = ['description', 'uuid', 'privacy', 'can_join']
        for key in optional_keys:
            if key in kwargs:
                if key == 'can_join':
                    parameters['canjoin'] = kwargs[key]
                    continue
                parameters[key] = kwargs[key]
        response = self.request('midas.community.create', parameters)
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

    def get_community_children(self, community_id, token=None):
        """Get the non-recursive children of the passed in community_id.

        :param token: A valid token for the user in question.
        :param community_id: The id of the requested community.
        :returns: List of the folders in the community.
        """
        parameters = dict()
        parameters['id'] = community_id
        if token:
            parameters['token'] = token
        response = self.request('midas.community.children', parameters)
        return response

    def list_communities(self, token=None):
        """List all communities visible to a user.

        :param token: (optional) A valid token for the user in question.
        :returns: The list of communities.
        """
        parameters = dict()
        if token:
            parameters['token'] = token
        response = self.request('midas.community.list', parameters)
        return response

    def create_folder(self, token, name, parent_id, **kwargs):
        """Create a folder at the destination specified.

        :param token: A valid token for the user in question.
        :param name: The name of the folder to be created.
        :param parent_id: The id of the targeted parent folder.
        :param description: (optional) The description text of the folder.
        :param uuid: (optional) The UUID for the folder. It will be generated
        if not given.
        :param privacy: (optional) The privacy state of the folder
        ('Public' or 'Private').
        :param reuse_existing: (optional) If true, will just return the
        existing folder if there is one with the name
        provided.
        :returns: Dictionary containing the details of the created folder.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parent_id
        parameters['description'] = ''
        optional_keys = ['description', 'uuid', 'privacy', 'reuse_existing']
        for key in optional_keys:
            if key in kwargs:
                if key == 'reuse_existing':
                    if kwargs[key]:
                        parameters['reuseExisting'] = kwargs[key]
                    continue
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

    def move_folder(self, token, folder_id, dest_folder_id):
        """Move a folder to the destination folder.

        :param token: A valid token for the user in question.
        :param folder_id: The id of the folder to be moved.
        :param dest_folder_id: The id of destination (new parent) folder.
        :returns: Dictionary containing the details of the moved folder.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = folder_id
        parameters['dstfolderid'] = dest_folder_id
        response = self.request('midas.folder.move', parameters)
        return response

    def create_item(self, token, name, parent_id, **kwargs):
        """Create an item to the server.

        :param token: A valid token for the user in question.
        :param name: The name of the item to be created.
        :param parent_id: The id of the destination folder.
        :param description: (optional) The description text of the item.
        :param uuid: (optional) The UUID for the item. It will be generated if
        not given.
        :param privacy: (optional) The privacy state of the item
        ('Public' or 'Private').
        :returns: Dictionary containing the details of the created item.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parent_id
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
        :param token: (optional) The authentication token of the user
        requesting the download.
        :param revision: (optional) The revision of the item to download, this
        defaults to HEAD.
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
        return filename, request.iter_content(chunk_size=10 * 1024)

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

    def get_item_metadata(self, item_id, token=None, revision=None):
        """Get the metadata associated with an item.

        :param item_id: The id of the item for which metadata will be returned
        :param token: (optional) A valid token for the user in question.
        :param revision: (optional) Revision of the item. Defaults to latest
        revision.
        :returns: List of dictionaries containing item metadata.
        """
        parameters = dict()
        parameters['id'] = item_id
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
        :param qualifier: (optional) The metadata qualifier. Defaults to empty
        string.
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
        :param dest_folder_id: The id of destination folder where the item is
        shared to.
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
        :param dest_folder_id: The id of destination folder where the item is
        moved to.
        :returns: Dictionary containing the details of the moved item.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        parameters['srcfolderid'] = src_folder_id
        parameters['dstfolderid'] = dest_folder_id
        response = self.request('midas.item.move', parameters)
        return response

    def search_item_by_name(self, name, token=None):
        """Return all items.

        :param name: The name of the item to search by.
        :param token: (optional) A valid token for the user in question.
        :returns: A list of all items with the given name.
        """
        parameters = dict()
        parameters['name'] = name
        if token:
            parameters['token'] = token
        response = self.request('midas.item.searchbyname', parameters)
        return response['items']

    def search_item_by_name_and_folder_name(self, name, folder_name, token=None):
        """Return all items with a given name and parent folder name.

        :param name: The name of the item to search by.
        :param folder_name: The name of the parent folder to search by.
        :param token: (optional) A valid token for the user in question.

        :returns: A list of all items with the given name and parent folder name.
        """
        parameters = dict()
        parameters['name'] = name
        parameters['folderName'] = folder_name
        if token:
            parameters['token'] = token
        response = self.request('midas.item.searchbynameandfoldername', parameters)
        return response['items']

    def create_link(self, token, folder_id, url, **kwargs):
        """Create a link bitstream.

        :param token: A valid token for the user in question.
        :param folder_id: The id of the folder in which to create a new item
        that will contain the link. The new item will have the same name as the
        URL unless an item name is supplied.
        :param url: The URL of the link you will create, will be used as the
        name of the bitstream and of the item unless an item name is supplied.
        :param item_name: (optional)  The name of the newly created item, if
        not supplied, the item will have the same name as the URL.
        :param length: (optional) The length in bytes of the file to which the
        link points.
        :param checksum: (optional) The MD5 checksum of the file to which the
        link points.
        :returns: The item information of the item created.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['folderid'] = folder_id
        parameters['url'] = url
        optional_keys = ['item_name', 'length', 'checksum']
        for key in optional_keys:
            if key in kwargs:
                if key == 'item_name':
                    parameters['itemname'] = kwargs[key]
                    continue
                parameters[key] = kwargs[key]
        response = self.request('midas.link.create', parameters)
        return response

    def generate_upload_token(self, token, item_id, filename, checksum=None):
        """Generate a token to use for upload.

        Midas uses a individual token for each upload. The token corresponds to
        the file specified and that file only. Passing the MD5 checksum allows
        the server to determine if the file is already in the asset store.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item in which to upload the file as a
        bitstream.
        :param filename: The name of the file to generate the upload token for.
        :param checksum: (optional) The checksum of the file to upload.
        :returns: String of the upload token.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemid'] = item_id
        parameters['filename'] = filename
        if not checksum is None:
            parameters['checksum'] = checksum
        response = self.request('midas.upload.generatetoken', parameters)
        return response['token']

    def perform_upload(self, uploadtoken, filename, **kwargs):
        """Upload a file into a given item (or just to the public folder if the
        item is not specified.

        :param uploadtoken: The upload token (returned by generate_upload_token)
        :param filename: The upload filename. Also used as the path to the file,
        if 'filepath' is not set.
        :param mode: (optional) Stream or multipart. Default is stream.
        :param folderid: (optional) The id of the folder to upload into.
        :param item_id: (optional) If set, will create a new revision in the
        existing item.
        :param revision: (optional) If set, will add a new file into an
        existing revision. Set this to "head" to add to the most recent
        revision.
        :param filepath: (optional) The path to the file.
        :returns: Dictionary containing the details of the item created or
        changed.
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
        :returns: Dictionary containing the search result. Notable is the
        dictionary item 'results', which is a list of item details.
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

    def add_condor_dag(self, token, batchmaketaskid, dagfilename,
                       dagmanoutfilename):
        """Adds a condor dag to the given batchmake task
        """
        parameters = dict()
        parameters['token'] = token
        parameters['batchmaketaskid'] = batchmaketaskid
        parameters['dagfilename'] = dagfilename
        parameters['outfilename'] = dagmanoutfilename
        response = self.request('midas.batchmake.add.condor.dag', parameters)
        return response

    def add_condor_job(self, token, batchmaketaskid, jobdefinitionfilename,
                       outputfilename, errorfilename, logfilename,
                       postfilename):
        """Adds a condor dag job to the condor dag associated with this
        batchmake task
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

        :param temp_token: The temporary token or id returned from normal login
        :param one_time_pass: The one-time pass to be sent to the underlying
        multi-factor engine.
        :returns: A standard token for interacting with the web api.
        """
        parameters = dict()
        parameters['mfaTokenId'] = temp_token
        parameters['otp'] = one_time_pass
        response = self.request('midas.mfa.otp.login', parameters)
        return response['token']


class ThumbnailCreatorDriver(BaseDriver):
    """Driver for the Midas thumbnailcreator module's API methods.
    """

    def create_big_thumbnail(self, token, bitstream_id, item_id, width=575):
        """Create a big thumbnail for the given bitstream with the given width.
        It is used as the main image of the given item and shown in the item
        view page.

        :param token: A valid token for the user in question.
        :param bitstream_id: The bitstream from which to create the thumbnail.
        :param item_id: The item on which to set the thumbnail.
        :param width: (optional) The width in pixels to which to resize (aspect
        ratio will be preserved). Defaults to 575.
        :returns: The ItemthumbnailDao object that was created.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['bitstreamId'] = bitstream_id
        parameters['itemId'] = item_id
        parameters['width'] = width
        response = self.request('midas.thumbnailcreator.create.big.thumbnail',
                                parameters)
        return response

    def create_small_thumbnail(self, token, item_id):
        """Create a 100x100 small thumbnail for the given item. It is used for
        preview purpose and displayed in the 'preview' and 'thumbnails'
        sidebar sections.

        :param token: A valid token for the user in question.
        :param item_id: The item on which to set the thumbnail.
        :returns: The item object (with the new thumbnail id) and the path
        where the newly created thumbnail is stored.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemId'] = item_id
        response = self.request('midas.thumbnailcreator.create.small.thumbnail',
                                parameters)
        return response


class SolrDriver(BaseDriver):
    """Driver for the Midas solr module's api methods.
    """

    def solr_advanced_search(self, query, token=None, limit=20):
        """Search item metadata using Apache Solr.

        :param query: The Apache Lucene search query.
        :param token: (optional) A valid token for the user in question.
        :param limit: (optional) The limit of the search.
        :returns: The list of items that match the search query.
        """
        parameters = dict()
        parameters['query'] = query
        parameters['limit'] = limit
        if token:
            parameters['token'] = token
        response = self.request('midas.solr.search.advanced', parameters)
        return response


class TrackerDriver(BaseDriver):
    """Driver for the Midas tracker module's api methods.
    """

    def associate_item_with_scalar_data(self, token, item_id, scalar_id,
                                        label):
        """Associate a result item with a particular scalar value.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item to associate with the scalar.
        :param scalar_id: Scalar id with which to associate the item.
        :param label: The label describing the nature of the association.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['scalarIds'] = scalar_id
        parameters['itemId'] = item_id
        parameters['label'] = label
        self.request('midas.tracker.item.associate', parameters)

    def add_scalar_data(self, token, community_id, producer_display_name,
                        metric_name, producer_revision, submit_time, value,
                        **kwargs):
        """Create a new scalar data point.

        :param token: A valid token for the user in question.
        :param community_id: The id of the community that owns the producer.
        :param producer_display_name: The display name of the producer.
        :param metric_name: The metric name that identifies which trend this
        point belongs to.
        :param producer_revision: The repository revision of the producer that
        produced this value.
        :param submit_time: The submit timestamp. Must be parsable with PHP
        strtotime().
        :param value: The value of the scalar.
        :param config_item_id: (optional) If this value pertains to a specific
        configuration item, pass its id here.
        :param test_dataset_id: (optional) If this value pertains to a
        specific test dataset, pass its id here.
        :param truth_dataset_id: (optional) If this value pertains to a
        specific ground truth dataset, pass its id here.
        :param silent: (optional) If true, do not perform threshold-based email
        notifications for this scalar.
        :param unofficial: (optional) If true, creates an unofficial scalar
        visible only to the user performing the submission.
        :param build_results_url: (optional) A URL for linking to build results
        for this submission.
        :param branch: (optional) The branch name in the source repository for
        this submission.
        :param params: (optional) Any key/value pairs that should be displayed
        with this scalar result.
        :type params: dict
        :param extra_urls: (optional) Other URL's that should be displayed with
        with this scalar result. Each element of the list should be a dict with
        the following keys: label, text, href
        :type extra_urls: list of dicts
        :returns: The scalar object that was created.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['communityId'] = community_id
        parameters['producerDisplayName'] = producer_display_name
        parameters['metricName'] = metric_name
        parameters['producerRevision'] = producer_revision
        parameters['submitTime'] = submit_time
        parameters['value'] = value
        optional_keys = [
            'config_item_id', 'test_dataset_id', 'truth_dataset_id', 'silent',
            'unofficial', 'build_results_url', 'branch', 'extra_urls', 'params']
        for key in optional_keys:
            if key in kwargs:
                if key == 'config_item_id':
                    parameters['configItemId'] = kwargs[key]
                elif key == 'test_dataset_id':
                    parameters['testDatasetId'] = kwargs[key]
                elif key == 'truth_dataset_id':
                    parameters['truthDatasetId'] = kwargs[key]
                elif key == 'build_results_url':
                    parameters['buildResultsUrl'] = kwargs[key]
                elif key == 'extra_urls':
                    parameters['extraUrls'] = json.dumps(kwargs[key])
                elif key == 'params':
                    parameters[key] = json.dumps(kwargs[key])
                elif key == 'silent':
                    if kwargs[key]:
                        parameters[key] = kwargs[key]
                elif key == 'unofficial':
                    if kwargs[key]:
                        parameters[key] = kwargs[key]
                else:
                    parameters[key] = kwargs[key]
        response = self.request('midas.tracker.scalar.add', parameters)
        return response

    def upload_json_results(self, token, filepath, community_id,
                            producer_display_name, metric_name,
                            producer_revision, submit_time, **kwargs):
        """Upload a JSON file containing numeric scoring results to be added
        as scalars. File is parsed and then deleted from the server.

        :param token: A valid token for the user in question.
        :param filepath: The path to the JSON file.
        :param community_id: The id of the community that owns the producer.
        :param producer_display_name: The display name of the producer.
        :param producer_revision: The repository revision of the producer
        that produced this value.
        :param submit_time: The submit timestamp. Must be parsable with PHP
        strtotime().
        :param config_item_id: (optional) If this value pertains to a specific
        configuration item, pass its id here.
        :param test_dataset_id: (optional) If this value pertains to a
        specific test dataset, pass its id here.
        :param truth_dataset_id: (optional) If this value pertains to a
        specific ground truth dataset, pass its id here.
        :param parent_keys: (optional) Semicolon-separated list of parent keys
        to look for numeric results under. Use '.' to denote nesting, like in
        normal javascript syntax.
        :param silent: (optional) If true, do not perform threshold-based email
        notifications for this scalar.
        :param unofficial: (optional) If true, creates an unofficial scalar
        visible only to the user performing the submission.
        :param build_results_url: (optional) A URL for linking to build results
        for this submission.
        :param branch: (optional) The branch name in the source repository for
        this submission.
        :param params: (optional) Any key/value pairs that should be displayed
        with this scalar result.
        :type params: dict
        :param extra_urls: (optional) Other URL's that should be displayed with
        with this scalar result. Each element of the list should be a dict with
        the following keys: label, text, href
        :type extra_urls: list of dicts
        :returns: The list of scalars that were created.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['communityId'] = community_id
        parameters['producerDisplayName'] = producer_display_name
        parameters['metricName'] = metric_name
        parameters['producerRevision'] = producer_revision
        parameters['submitTime'] = submit_time
        optional_keys = [
            'config_item_id', 'test_dataset_id', 'truth_dataset_id', 'silent',
            'unofficial', 'build_results_url', 'branch', 'extra_urls', 'params']
        for key in optional_keys:
            if key in kwargs:
                if key == 'config_item_id':
                    parameters['configItemId'] = kwargs[key]
                elif key == 'test_dataset_id':
                    parameters['testDatasetId'] = kwargs[key]
                elif key == 'truth_dataset_id':
                    parameters['truthDatasetId'] = kwargs[key]
                elif key == 'parent_keys':
                    parameters['parentKeys'] = kwargs[key]
                elif key == 'build_results_url':
                    parameters['buildResultsUrl'] = kwargs[key]
                elif key == 'extra_urls':
                    parameters['extraUrls'] = json.dumps(kwargs[key])
                elif key == 'params':
                    parameters[key] = json.dumps(kwargs[key])
                elif key == 'silent':
                    if kwargs[key]:
                        parameters[key] = kwargs[key]
                elif key == 'unofficial':
                    if kwargs[key]:
                        parameters[key] = kwargs[key]
                else:
                    parameters[key] = kwargs[key]
        file_payload = open(filepath, 'rb')
        response = self.request('midas.tracker.results.upload.json',
                                parameters, file_payload)
        return response
