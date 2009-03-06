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

HTTP_MAPPINGS = {
    100: '100 CONTINUE',
    101: '101 SWITCHING PROTOCOLS',
    200: '200 OK',
    201: '201 CREATED',
    202: '202 ACCEPTED',
    203: '203 NON-AUTHORITATIVE INFORMATION',
    204: '204 NO CONTENT',
    205: '205 RESET CONTENT',
    206: '206 PARTIAL CONTENT',
    300: '300 MULTIPLE CHOICES',
    301: '301 MOVED PERMANENTLY',
    302: '302 FOUND',
    303: '303 SEE OTHER',
    304: '304 NOT MODIFIED',
    305: '305 USE PROXY',
    306: '306 RESERVED',
    307: '307 TEMPORARY REDIRECT',
    400: '400 BAD REQUEST',
    401: '401 UNAUTHORIZED',
    402: '402 PAYMENT REQUIRED',
    403: '403 FORBIDDEN',
    404: '404 NOT FOUND',
    405: '405 METHOD NOT ALLOWED',
    406: '406 NOT ACCEPTABLE',
    407: '407 PROXY AUTHENTICATION REQUIRED',
    408: '408 REQUEST TIMEOUT',
    409: '409 CONFLICT',
    410: '410 GONE',
    411: '411 LENGTH REQUIRED',
    412: '412 PRECONDITION FAILED',
    413: '413 REQUEST ENTITY TOO LARGE',
    414: '414 REQUEST-URI TOO LONG',
    415: '415 UNSUPPORTED MEDIA TYPE',
    416: '416 REQUESTED RANGE NOT SATISFIABLE',
    417: '417 EXPECTATION FAILED',
    500: '500 INTERNAL SERVER ERROR',
    501: '501 NOT IMPLEMENTED',
    502: '502 BAD GATEWAY',
    503: '503 SERVICE UNAVAILABLE',
    504: '504 GATEWAY TIMEOUT',
    505: '505 HTTP VERSION NOT SUPPORTED',
}


class NotFound(Exception):
    pass


class Request(object):
    GET = {}
    POST = {}
    PUT = {}
    DELETE = {}
    
    def __init__(self, environ):
        self._environ = environ
        self.setup_self()
    
    def setup_self(self):
        self.path = add_slash(self._environ.get('PATH_INFO', ''))
        self.method = self._environ.get('REQUEST_METHOD', 'GET')
        self.query = self._environ.get('QUERY_STRING', '')
        
        self.GET = build_query_dict(self.query)


def build_query_dict(query_string):
    pairs = query_string.split('&')
    query_dict = {}
    pair_re = re.compile('^(?P<key>[^=]*?)=(?P<value>.*)')
    
    for pair in pairs:
        match = pair_re.search(pair)
        
        if match is not None:
            match_data = match.groupdict()
            query_dict[match_data['key']] = match_data['value']
    
    return query_dict


def handle_request(environ, start_response):
    """The main handler. Dispatches to the user's code."""
    request = Request(environ)
    
    try:
        (re_url, url, callback), kwargs = find_matching_url(request)
    except NotFound:
        return not_found(environ, start_response)
    
    output = callback(request, **kwargs)
    ct = 'text/html'
    status = 200
    
    try:
        ct = callback.content_type
    except AttributeError:
        pass
    
    try:
        status = callback.status
    except AttributeError:
        pass
    
    start_response(HTTP_MAPPINGS.get(status), [('Content-Type', ct)])
    return output


def find_matching_url(request):
    if not request.method in REQUEST_MAPPINGS:
        raise NotFound("The HTTP request method '%s' is not supported." % request.method)
    
    for url_set in REQUEST_MAPPINGS[request.method]:
        match = url_set[0].search(request.path)
        
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
