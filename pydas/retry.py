import pydas.exceptions

def reauth(fn):
    """
    this decorator will detect a stale token and renew the token if possible,
    then retry the failed api call.
    """
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kw):
        try:
            return fn(*args, **kw)
        except pydas.exceptions.PydasException as pe:
            if pe.value.find('Invalid token') > -1:
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
                return fn(*args, **kw)
            else:
                raise pe
    return wrapper
