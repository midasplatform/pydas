"""
This module is for the drivers that actually do the work of communication with
the Midas server. Any drivers that are implemented should use the utility
functions provided in pydas.drivers.BaseDriver by inheriting from that class.
"""
import simplejson as json
import requests as http
import os
from pydas.exceptions import PydasException

class BaseDriver(object):
    """
    Base class for the midas api drivers.
    """

    def __init__(self, url=""):
        """
        Constructor
        """
        self._api_suffix = '/api/json?method='
        self._url = url
        self._debug = False

    @property
    def url(self):
        """
        Getter for the url
        """
        return self._url

    @url.setter
    def url(self, value):
        """
        Set the url
        """
        self._url = value

    @property
    def full_url(self):
        """
        Return the full path the the url (including the api extensions).
        """
        return self._url + self._api_suffix

    def request(self, method, parameters=None, file_payload=None):
        """
        Do the generic processing of a request to the server. If file_payload
        is specified, it will be PUT to the server.
        """
        method_url = self.full_url + method
        request = None
        if file_payload:
            request = http.put(method_url,
                               data=file_payload.read(),
                               params=parameters)
        else:
            request = http.post(method_url, params=parameters)
        code = request.status_code
        if self._debug:
            print request.content
        if code != 200:
            raise PydasException("Request failed with HTTP error code "
                                 "%d" % code)
        response = json.loads(request.content)

        if response['stat'] != 'ok':
            raise PydasException("Request failed with Midas error code "
                                 "%s: %s" % (response['code'],
                                             response['message']))
        return response['data']

class CoreDriver(BaseDriver):
    """
    Driver for the core API methods of Midas.
    """
    
    def get_server_version(self):
        """
        Get the version from the server
        """
        response = self.request('midas.version')
        return response['version']

    def get_server_info(self):
        """
        Get info from the server (this is an alias to getVersion on most
        platforms, but it returns the whole dictionary).
        """
        response = self.request('midas.info')
        return response['version']

    def get_default_api_key(self, email, password):
        """
        Gets the default api key given an email and password
        """
        parameters = dict()
        parameters['email'] = email
        parameters['password'] = password
        response = self.request('midas.user.apikey.default', parameters)
        return response['apikey']

    def login_with_api_key(self, email, apikey, application='Default'):
        """
        Login and get a token using an email and apikey. If you do not specify
        a specific application, 'default' will be used
        """
        parameters = dict()
        parameters['email'] = email
        parameters['apikey'] = apikey
        parameters['appname'] = application
        response = self.request('midas.login', parameters)
        return response['token']

    def list_user_folders(self, token):
        """
        Use a users token to list the curent folders.
        """
        parameters = dict()
        parameters['token'] = token
        response = self.request('midas.user.folders', parameters)
        return response

    def create_folder(self, token, name, parent, **kwargs):
        """
        Create a folder
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parent
        parameters['description'] = ''
        optional_keys = ('description', 'uuid', 'privacy')
        for key in optional_keys:
            if kwargs.has_key(key):
                parameters[key] = kwargs[key]
        response = self.request('midas.folder.create', parameters)
        return response
    
    def generate_upload_token(self, token, itemid, filename, checksum=None):
        """
        Generate a token to use for upload.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemid'] = itemid
        parameters['filename'] = filename
        if not checksum == None:
            parameters['checksum'] = checksum
        response = self.request('midas.upload.generatetoken', parameters)
        return response['token']

    def create_item(self, token, name, parentid, **kwargs):
        """
        Create an item to hold bitstreams.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parentid
        parameters['privacy'] = 'Public'
        optional_keys = ('description', 'uuid', 'privacy')
        for key in optional_keys:
            if kwargs.has_key(key):
                parameters[key] = kwargs[key]
        response = self.request('midas.item.create', parameters)
        return response

    def perform_upload(self, uploadtoken, filename, **kwargs):
        """
        Upload a file into a given item (or just to the public folder if the
        item is not specified.
        """
        parameters = dict()
        parameters['uploadtoken'] = uploadtoken
        parameters['filename'] = filename
        parameters['revision'] = 'head'

        optional_keys = ('mode', 'folderid', 'itemid', 'revision')
        for key in optional_keys:
            if kwargs.has_key(key):
                parameters[key] = kwargs[key]
        
        # We may want a different name than path
        if kwargs.has_key('filepath'):
            file_payload = open(kwargs['filepath'])
        else:
            file_payload = open(filename)
        # Arcane getting of the file size using fstat. More details can be
        # found in the python library docs
        parameters['length'] = os.fstat(file_payload.fileno()).st_size

        response = self.request('midas.upload.perform', parameters,
                                file_payload)
        return response

    def get_item_metadata(self, item, token=None, revision=None):
        """
        Get the metadata associated with an item.
        """
        parameters = dict()
        parameters['id'] = item
        if token:
            parameters['token'] = token
        if revision:
            parameters['revision'] = revision
        response = self.request('midas.item.getmetadata', parameters)
        return response

