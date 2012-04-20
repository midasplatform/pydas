import pydas.exceptions
import time

def reauth(fn):
    """
    this decorator will detect a stale token and renew the token if possible,
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
            print "Waiting 30 seconds, then retrying request"

            # wait 30 seconds before retrying
            time.sleep(30) 

            # renew the token
            # get the instance of the CoreDriver and set it as "that"
            that = args[0]
            token = that.login_with_api_key(that.__class__.email,
                                            that.__class__.apikey)

            # now fix up the arguments of the original call to use the renewed token
            argsList = list(args)
            argsList[2]['token'] = token
            args = tuple(argsList)

            # try the api call again
            retVal = fn(*args, **kw)
            return retVal
    return wrapper
