"""
The itty-bitty Python web framework.

Totally ripping off Sintra, the Python way.
"""
import re

__author__ = 'Daniel Lindsley'
__version__ = ('0', '0', '1')
__license__ = 'MIT'


REQUEST_MAPPINGS = {
    'GET': [],
    'POST': [],
    'PUT': [],
    'DELETE': [],
}


class NotFound(Exception):
    pass


def handle_request(environ, start_response):
    """The main handler. Dispatches to the user's code."""
    try:
        (re_url, url, callback), kwargs = find_matching_url(environ)
    except NotFound:
        return not_found(environ, start_response)
    
    # DRL_FIXME: Allow other statuses.
    start_response('200 OK', [('Content-Type', 'text/html')])
    return callback(**kwargs)


def find_matching_url(environ):
    request_method = environ.get('REQUEST_METHOD', 'GET')
    
    if not request_method in REQUEST_MAPPINGS:
        raise NotFound("The HTTP request method '%s' is not supported." % request_method)
    
    path = add_slash(environ.get('PATH_INFO', ''))
    
    for url_set in REQUEST_MAPPINGS[request_method]:
        match = url_set[0].search(path)
        
        if match is not None:
            return (url_set, match.groupdict())
    
    raise NotFound("Sorry, nothing here.")


def add_slash(url):
    if not url.endswith('/'):
        url = url + '/'
    return url


def not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']


# Decorators

def get(url):
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['GET'].append((re_url, url, new))
        return new
    return wrapped


def post(url):
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['POST'].append((re_url, url, new))
        return new
    return wrapped


# Sample server

def run_itty(host='localhost', port=8080):
    """
    Runs the itty web server.
    
    Accepts an optional host (string) and port (integer) parameters.
    
    Uses Python's built-in wsgiref implementation. Easily replaced with other
    WSGI server implementations.
    """
    print 'itty starting up...'
    print 'Use Ctrl-C to quit.'
    print
    
    try:
        from wsgiref.simple_server import make_server
        srv = make_server(host, port, handle_request)
        srv.serve_forever()
    except KeyboardInterrupt:
        print "Shuting down..."
        import sys
        sys.exit()


if __name__ == '__main__':
    run_itty()
