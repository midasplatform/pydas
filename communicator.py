import simplejson as json
import urllib
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

    def makeRequest(self, method):
        """
        Do the generic processing of a request to the server
        """
        request = urllib.urlopen(self.serverUrl + self.apiSuffix + method)
        code = request.getcode()
        if code != 200:
            raise PydasException("Request failed with HTTP error code %d" % code)

        response = json.loads(request.read())

        if response['stat'] != 'ok':
            raise PydasException("Request failed with Midas error code %s: %s" % (response['code'],
                                                                                  response['message']))
        return response['data']
        
    def getServerVersion(self):
        """
        Get the version from the server
        """
        response = self.makeRequest('midas.version')
        return response['version']
