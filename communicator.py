import simplejson as json
import requests as http
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

    def makeRequest(self, method, parameters=None):
        """
        Do the generic processing of a request to the server
        """
        url = self.serverUrl + self.apiSuffix + method
        request = None
        if parameters:
            request = http.post(url, headers=parameters)
        else:
            request = http.post(url, headers=parameters)
        code = request.status_code
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
    
    def generateUploadToken(self, token, itemid, filename, checksum=None):
        """
        Generate a token to use for upload.
        """
        parameters = dict()
        parameters['token'] = token
        parameters['itemid'] = itemid
        parameters['filename'] = filename
        response = self.makeRequest('midas.upload.generatetoken', parameters)
        return response

    def createItem():
        """
        """
        
