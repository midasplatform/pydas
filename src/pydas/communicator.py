import simplejson as json
import requests as http
import os
from exceptions import PydasException

class Communicator(object):
    """
    Class for exchanging data with a midas server.
    """

    def __init__(self, url=""):
        """
        Constructor
        """
        self.apiSuffix = '/api/json?method='
        self.serverUrl = url
        self.debug = False

    def makeRequest(self, method, parameters=None, file=None):
        """
        Do the generic processing of a request to the server
        """
        url = self.serverUrl + self.apiSuffix + method
        request = None
        if file:
            request = http.put(url, data=file.read(), params=parameters)
        else:
            request = http.post(url, params=parameters)
        code = request.status_code
        if self.debug:
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
        
    def getServerVersion(self):
        """
        Get the version from the server
        """
        response = self.makeRequest('midas.version')
        return response['version']

    def getServerInfo(self):
        """
        Get info from the server (this is an alias to getVersion on most
        platforms, but it returns the whole dictionary).
        """
        response = self.makeRequest('midas.info')
        return response

    def getDefaultApiKey(self, email, password):
        """
        Gets the default api key given an email and password
        """
        parameters = dict()
        parameters['email'] = email
        parameters['password'] = password
        response = self.makeRequest('midas.user.apikey.default', parameters)
        return response['apikey']

    def loginWithApiKey(self, email, apikey, application='Default'):
        """
        Login and get a token using an email and apikey. If you do not specify
        a specific application, 'default' will be used
        """
        parameters = dict()
        parameters['email'] = email
        parameters['apikey'] = apikey
        parameters['appname'] = application
        response = self.makeRequest('midas.login', parameters)
        return response['token']

    def listUserFolders(self, token):
        """
        Use a users token to list the curent folders.
        """
        parameters = dict()
        parameters['token'] = token
        response = self.makeRequest('midas.user.folders', parameters)
        return response

    def createFolder(self, token, name, parent, description=None,
                     uuid=None, privacy=None):
        """
        Create a folder
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parent
        if description:
            parameters['description'] = description
        else:
            parameters['desrciption'] = ''
        if uuid:
            parameters['uuid'] = uuid
        if privacy:
            parameters['privacy'] = privacy
        response = self.makeRequest('midas.folder.create', parameters)
    
    def generateUploadToken(self, token, itemid, filename, checksum=None):
        """
        Generate a token to use for upload.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemid'] = itemid
        parameters['filename'] = filename
        if not checksum == None:
            parameters['checksum'] = checksum
        response = self.makeRequest('midas.upload.generatetoken', parameters)
        return response

    def createItem(self, token, name, parentid, description=None, uuid=None,
                   privacy='Public'):
        """
        Create an item to hold bitstreams.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['name'] = name
        parameters['parentid'] = parentid
        parameters['privacy'] = privacy
        if not description == None:
            parameters['description'] = description
        if not uuid == None:
            parameters['uuid'] = uuid
        response = self.makeRequest('midas.item.create', parameters)
        return response

    def performUpload(self, uploadtoken, filename, length, filepath=None,
                      mode=None, folderid=None, itemid=None, revision=None):
        """
        Upload a file into a given item (or just to the public folder if the
        item is not specified.
        """
        parameters = dict()
        parameters['uploadtoken'] = uploadtoken
        parameters['filename'] = filename
        parameters['length'] = length
        if not mode == None:
            parameters['mode'] = mode
        if not folderid == None:
            parameters['folderid'] = folderid
        if not itemid == None:
            parameters['itemid'] = itemid
        if not revision == None:
            parameters['revision'] = revision
        
        # We may want a different name than path
        if not filepath == None:
            file = open(filepath)
        else:
            file = open(filename)

        response = self.makeRequest('midas.upload.perform', parameters, file)
        return response

    def getItemMetadata(self, item, token=None, revision=None):
        """
        Get the metadata associated with an item.
        """
        parameters = dict()
        parameters['id'] = item
        if token:
            parameters['token'] = token
        if revision:
            parameters['revision'] = revision
        response = self.makeRequest('midas.item.getmetadata', parameters)
        return response

