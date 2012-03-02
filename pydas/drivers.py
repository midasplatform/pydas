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

    def login_with_api_key(self, email, apikey, application='Default'):
        """ Login and get a token.

        If you do not specify a specific application, 'Default' will be used.

        :param email: The email of the user.
        :param password: A valid api-key assigned to the user.
        :param application: (optional) Application designated for this api key.
        :returns: String of the token to be used for interaction with the api until expiration.
        """
        parameters = dict()
        parameters['email'] = email
        parameters['apikey'] = apikey
        parameters['appname'] = application
        response = self.request('midas.login', parameters)
        return response['token']

    def list_user_folders(self, token):
        """List the folders in the users home area.

        :param token: A valid token for the user in question.
        :returns: List of dictionaries containing foder information.
        """
        parameters = dict()
        parameters['token'] = token
        response = self.request('midas.user.folders', parameters)
        return response

    def create_folder(self, token, name, parent, **kwargs):
        """Create a folder at the destination specified.

        :param token: A valid token for the user in question.
        :param name: The name of the folder to be created.
        :param parent: The id of the targeted parent folder.
        :param description: (optional) The description text of the folder.
        :param uuid: (optional) The uuid for the folder. It will be generated if not given.
        :param privacy: (optional) The privacy state of the folder ('Public' or 'Private').
        :returns: Dictionary containing the details of the created folder.
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
        """Generate a token to use for upload.
        
        Midas uses a individual token for each upload. The token corresponds to
        the file specified and that file only. Passing the MD5 checksum allows
        the server to determine if the file is already in the assetstore.

        :param token: A valid token for the user in question.
        :param itemid: The id of the item in which to upload the file as a bitstream.
        :param filename: The name of the file to generate the upload token for.
        :param checksum: (optional) The checksum of the file to upload.
        :returns: String of the upload token.
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
        """Create an item to the server.

        :param token: A valid token for the user in question.
        :param name: The name of the item to be created.
        :param parentid: The id of the destination folder.
        :param description: (optional) The description text of the item.
        :param uuid: (optional) The uuid for the item. It will be generated if not given.
        :param privacy: (optional) The privacy state of the item ('Public' or 'Private').
        :returns: Dictionary containing the details of the created item.
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

    def delete_item(self, token, item_id):
        """Delete the item with the passed in item_id.

        :param token: A valid token for the user in question.
        :param item_id: The id of the item to be deleted.
        :returns: Dictionary of the response indicating success.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = item_id
        response = self.request('midas.item.delete', parameters)
        return response

    def folder_children(self, token, folder_id):
        """Get the non-recursive children of the passed in folder_id.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['id'] = folder_id
        response = self.request('midas.folder.children', parameters)
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

class BatchmakeDriver(BaseDriver):
    """
    Driver for the Midas batchmake module's API methods.
    """

    def add_condor_dag(self, token, batchmaketaskid, dagfilename, dagmanoutfilename):
        """
        Adds a condor dag to the given batchmake task
        """
        parameters = dict()
        parameters['token'] = token
        parameters['batchmaketaskid'] = batchmaketaskid
        parameters['dagfilename'] = dagfilename
        parameters['outfilename'] = dagmanoutfilename
        response = self.request('midas.batchmake.add.condor.dag', parameters)
        return response

    def add_condor_job(self, token, batchmaketaskid, jobdefinitionfilename, outputfilename, errorfilename, logfilename, postfilename):
        """
        Adds a condor dag job to the condor dag associated with this batchmake task
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
    """
    Driver for the Midas dicomextractor module's API methods.
    """

    def extract_dicommetadata(self, token, itemid):
        """
        Extracts dicom metadata from the given item
        """
        parameters = dict()
        parameters['token'] = token
        parameters['item'] = itemid
        response = self.request('midas.dicomextractor.extract', parameters)
        return response
