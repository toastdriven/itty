"""
The itty-bitty Python framework.

Totally ripping off Sintra, the Python way.
"""

__author__ = 'Daniel Lindsley'
__version__ = ('0', '0', '1')
__license__ = 'MIT'


REQUEST_MAPPINGS = {
    'GET': {},
    'POST': {},
    'PUT': {},
    'DELETE': {},
}


class NotFound(Exception):
    pass


def handle_request(environ, start_response):
    """The main handler. Dispatches to the user's code."""
    try:
        callback = find_matching_url(environ)
    except NotFound:
        return not_found(environ, start_response)
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return callback()


def find_matching_url(environ):
    request_method = environ.get('REQUEST_METHOD', 'GET')
    
    if not request_method in REQUEST_MAPPINGS:
        raise NotFound("The HTTP request method '%s' is not supported." % request_method)
    
    path = environ.get('PATH_INFO', '')
    
    for url, method in REQUEST_MAPPINGS[request_method].items():
        if url == path:
            return method
    
    raise NotFound("Sorry, nothing here.")


def not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']


# Decorators

def get(url):
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        REQUEST_MAPPINGS['GET'][url] = new
        return new
    return wrapped

def post(url):
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        REQUEST_MAPPINGS['POST'][url] = new
        return new
    return wrapped


def run_itty():
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, handle_request)
    srv.serve_forever()


if __name__ == '__main__':
    run_itty()
