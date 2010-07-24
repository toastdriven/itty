"""
The itty-bitty Python web framework.

Totally ripping off Sintra, the Python way. Very useful for small applications,
especially web services. Handles basic HTTP methods (PUT/DELETE too!). Errs on
the side of fun and terse.


Example Usage::

    from itty import get, run_itty

      @get('/')
      def index(request):
          return 'Hello World!'

      run_itty()


Thanks go out to Matt Croydon & Christian Metts for putting me up to this late
at night. The joking around has become reality. :)
"""
import cgi
import mimetypes
import os
import re
import StringIO
import sys
import traceback
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

__author__ = 'Daniel Lindsley'
__version__ = ('0', '6', '9')
__license__ = 'BSD'


REQUEST_MAPPINGS = {
    'GET': [],
    'POST': [],
    'PUT': [],
    'DELETE': [],
}

ERROR_HANDLERS = {}

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

HTTP_MAPPINGS = {
    100: 'CONTINUE',
    101: 'SWITCHING PROTOCOLS',
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    300: 'MULTIPLE CHOICES',
    301: 'MOVED PERMANENTLY',
    302: 'FOUND',
    303: 'SEE OTHER',
    304: 'NOT MODIFIED',
    305: 'USE PROXY',
    306: 'RESERVED',
    307: 'TEMPORARY REDIRECT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLICT',
    410: 'GONE',
    411: 'LENGTH REQUIRED',
    412: 'PRECONDITION FAILED',
    413: 'REQUEST ENTITY TOO LARGE',
    414: 'REQUEST-URI TOO LONG',
    415: 'UNSUPPORTED MEDIA TYPE',
    416: 'REQUESTED RANGE NOT SATISFIABLE',
    417: 'EXPECTATION FAILED',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPPORTED',
}


class RequestError(Exception):
    """A base exception for HTTP errors to inherit from."""
    status = 404
    
    def __init__(self, message, hide_traceback=False):
        super(RequestError, self).__init__(message)
        self.hide_traceback = hide_traceback


class Forbidden(RequestError):
    status = 403


class NotFound(RequestError):
    status = 404
    
    def __init__(self, message, hide_traceback=True):
        super(NotFound, self).__init__(message)
        self.hide_traceback = hide_traceback


class AppError(RequestError):
    status = 500


class Redirect(RequestError):
    """
    Redirects the user to a different URL.
    
    Slightly different than the other HTTP errors, the Redirect is less
    'OMG Error Occurred' and more 'let's do something exceptional'. When you
    redirect, you break out of normal processing anyhow, so it's a very similar
    case."""
    status = 302
    url = ''
    
    def __init__(self, url):
        self.url = url
        self.args = ["Redirecting to '%s'..." % self.url]


class lazyproperty(object):
    """A property whose value is computed only once. """
    def __init__(self, function):
        self._function = function

    def __get__(self, obj, _=None):
        if obj is None:
            return self
        
        value = self._function(obj)
        setattr(obj, self._function.func_name, value)
        return value


class Request(object):
    """An object to wrap the environ bits in a friendlier way."""
    GET = {}
    
    def __init__(self, environ, start_response):
        self._environ = environ
        self._start_response = start_response
        self.setup_self()
    
    def setup_self(self):
        self.path = add_slash(self._environ.get('PATH_INFO', ''))
        self.method = self._environ.get('REQUEST_METHOD', 'GET').upper()
        self.query = self._environ.get('QUERY_STRING', '')
        self.content_length = 0
        
        try:
            self.content_length = int(self._environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            pass
        
        self.GET = self.build_get_dict()
    
    @lazyproperty
    def POST(self):
        return self.build_complex_dict()
    
    @lazyproperty
    def PUT(self):
        return self.build_complex_dict()
    
    @lazyproperty
    def body(self):
        """Content of the request."""
        return self._environ['wsgi.input'].read(self.content_length)
    
    def build_get_dict(self):
        """Takes GET data and rips it apart into a dict."""
        raw_query_dict = parse_qs(self._environ['QUERY_STRING'], keep_blank_values=1)
        query_dict = {}
        
        for key, value in raw_query_dict.items():
            if len(value) <= 1:
                query_dict[key] = value[0]
            else:
                # Since it's a list of multiple items, we must have seen more than
                # one item of the same name come in. Store all of them.
                query_dict[key] = value
        
        return query_dict
    
    
    def build_complex_dict(self):
        """Takes POST/PUT data and rips it apart into a dict."""
        raw_data = cgi.FieldStorage(fp=StringIO.StringIO(self.body), environ=self._environ)
        query_dict = {}
        
        for field in raw_data:
            if isinstance(raw_data[field], list):
                # Since it's a list of multiple items, we must have seen more than
                # one item of the same name come in. Store all of them.
                query_dict[field] = [fs.value for fs in raw_data[field]]
            elif raw_data[field].filename:
                # We've got a file.
                query_dict[field] = raw_data[field]
            else:
                query_dict[field] = raw_data[field].value
        
        return query_dict


class Response(object):
    headers = []
    
    def __init__(self, output, headers=None, status=200, content_type='text/html'):
        self.output = output
        self.content_type = content_type
        self.status = status
        self.headers = []
        
        if headers and isinstance(headers, list):
            self.headers = headers
    
    def add_header(self, key, value):
        self.headers.append((key, value))
    
    def send(self, start_response):
        status = "%d %s" % (self.status, HTTP_MAPPINGS.get(self.status))
        headers = [('Content-Type', "%s; charset=utf-8" % self.content_type)] + self.headers
        final_headers = []
        
        # Because Unicode is unsupported...
        for header in headers:
            final_headers.append((self.convert_to_ascii(header[0]), self.convert_to_ascii(header[1])))
        
        start_response(status, final_headers)
        
        if isinstance(self.output, unicode):
            return self.output.encode('utf-8')
        else:
            return self.output
    
    def convert_to_ascii(self, data):
        if isinstance(data, unicode):
            try:
                return data.encode('us-ascii')
            except UnicodeError, e:
                raise
        else:
            return str(data)


def handle_request(environ, start_response):
    """The main handler. Dispatches to the user's code."""
    try:
        request = Request(environ, start_response)
    except Exception, e:
        return handle_error(e)
    
    try:
        (re_url, url, callback), kwargs = find_matching_url(request)
        response = callback(request, **kwargs)
    except Exception, e:
        return handle_error(e, request)
    
    if not isinstance(response, Response):
        response = Response(response)
    
    return response.send(start_response)


def handle_error(exception, request=None):
    """If an exception is thrown, deal with it and present an error page."""
    if request is None:
        request = {'_environ': {'PATH_INFO': ''}}
    
    if not getattr(exception, 'hide_traceback', False):
        (e_type, e_value, e_tb) = sys.exc_info()
        message = "%s occurred on '%s': %s\nTraceback: %s" % (
            exception.__class__,
            request._environ['PATH_INFO'],
            exception,
            ''.join(traceback.format_exception(e_type, e_value, e_tb))
        )
        request._environ['wsgi.errors'].write(message)
    
    if isinstance(exception, RequestError):
        status = getattr(exception, 'status', 404)
    else:
        status = 500
    
    if status in ERROR_HANDLERS:
        return ERROR_HANDLERS[status](request, exception)
    
    return not_found(request, exception)


def find_matching_url(request):
    """Searches through the methods who've registed themselves with the HTTP decorators."""
    if not request.method in REQUEST_MAPPINGS:
        raise NotFound("The HTTP request method '%s' is not supported." % request.method)
    
    for url_set in REQUEST_MAPPINGS[request.method]:
        match = url_set[0].search(request.path)
        
        if match is not None:
            return (url_set, match.groupdict())
    
    raise NotFound("Sorry, nothing here.")


def add_slash(url):
    """Adds a trailing slash for consistency in urls."""
    if not url.endswith('/'):
        url = url + '/'
    return url


def content_type(filename):
    """
    Takes a guess at what the desired mime type might be for the requested file.
    
    Mostly only useful for static media files.
    """
    ct = 'text/plain'
    ct_guess = mimetypes.guess_type(filename)
    
    if ct_guess[0] is not None:
        ct = ct_guess[0]
    
    return ct


def static_file(filename, root=MEDIA_ROOT):
    """
    Fetches a static file from the filesystem, relative to either the given
    MEDIA_ROOT or from the provided root directory.
    """
    if filename is None:
        raise Forbidden("You must specify a file you'd like to access.")
    
    # Strip the '/' from the beginning/end.
    valid_path = filename.strip('/')
    
    # Kill off any character trying to work their way up the filesystem.
    valid_path = valid_path.replace('//', '/').replace('/./', '/').replace('/../', '/')
    
    desired_path = os.path.join(root, valid_path)
    
    if not os.path.exists(desired_path):
        raise NotFound("File does not exist.")
    
    if not os.access(desired_path, os.R_OK):
        raise Forbidden("You do not have permission to access this file.")
    
    ct = str(content_type(desired_path))
    
    # Do the text types as a non-binary read.
    if ct.startswith('text') or ct.endswith('xml') or ct.endswith('json'):
        return open(desired_path, 'r').read()
    
    # Fall back to binary for everything else.
    return open(desired_path, 'rb').read()


# Static file handler

def serve_static_file(request, filename, root=MEDIA_ROOT, force_content_type=None):
    """
    Basic handler for serving up static media files.
    
    Accepts an optional ``root`` (filepath string, defaults to ``MEDIA_ROOT``) parameter.
    Accepts an optional ``force_content_type`` (string, guesses if ``None``) parameter.
    """
    file_contents = static_file(filename, root)
    
    if force_content_type is None:
        ct = content_type(filename)
    else:
        ct = force_content_type
    
    return Response(file_contents, content_type=ct)


# Decorators

def get(url):
    """Registers a method as capable of processing GET requests."""
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['GET'].append((re_url, url, new))
        return new
    return wrapped


def post(url):
    """Registers a method as capable of processing POST requests."""
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['POST'].append((re_url, url, new))
        return new
    return wrapped


def put(url):
    """Registers a method as capable of processing PUT requests."""
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['PUT'].append((re_url, url, new))
        new.status = 201
        return new
    return wrapped


def delete(url):
    """Registers a method as capable of processing DELETE requests."""
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['DELETE'].append((re_url, url, new))
        return new
    return wrapped


def error(code):
    """Registers a method for processing errors of a certain HTTP code."""
    def wrapped(method):
        def new(*args, **kwargs):
            return method(*args, **kwargs)
        # Register.
        ERROR_HANDLERS[code] = new
        return new
    return wrapped


# Error handlers

@error(403)
def forbidden(request, exception):
    response = Response('Forbidden', status=403, content_type='text/plain')
    return response.send(request._start_response)


@error(404)
def not_found(request, exception):
    response = Response('Not Found', status=404, content_type='text/plain')
    return response.send(request._start_response)


@error(500)
def app_error(request, exception):
    response = Response('Application Error', status=500, content_type='text/plain')
    return response.send(request._start_response)


@error(302)
def redirect(request, exception):
    response = Response('', status=302, content_type='text/plain', headers=[('Location', exception.url)])
    return response.send(request._start_response)


# Servers Adapters

def wsgiref_adapter(host, port):
    from wsgiref.simple_server import make_server
    srv = make_server(host, port, handle_request)
    srv.serve_forever()


def appengine_adapter(host, port):
    from google.appengine.ext.webapp import util
    util.run_wsgi_app(handle_request)


def cherrypy_adapter(host, port):
    # Experimental (Untested).
    from cherrypy import wsgiserver
    server = wsgiserver.CherryPyWSGIServer((host, port), handle_request)
    server.start()


def flup_adapter(host, port):
    # Experimental (Untested).
    from flup.server.fcgi import WSGIServer
    WSGIServer(handle_request, bindAddress=(host, port)).run()


def paste_adapter(host, port):
    # Experimental (Untested).
    from paste import httpserver
    httpserver.serve(handle_request, host=host, port=str(port))


def twisted_adapter(host, port):
    from twisted.web import server, wsgi
    from twisted.python.threadpool import ThreadPool
    from twisted.internet import reactor
    
    thread_pool = ThreadPool()
    thread_pool.start()
    reactor.addSystemEventTrigger('after', 'shutdown', thread_pool.stop)
    
    ittyResource = wsgi.WSGIResource(reactor, thread_pool, handle_request)
    site = server.Site(ittyResource)
    reactor.listenTCP(port, site)
    reactor.run()


def diesel_adapter(host, port):
    # Experimental (Mostly untested).
    from diesel.protocols.wsgi import WSGIApplication
    app = WSGIApplication(handle_request, port=int(port))
    app.run()


def tornado_adapter(host, port):
    # Experimental (Mostly untested).
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
    
    container = WSGIContainer(handle_request)
    http_server = HTTPServer(container)
    http_server.listen(port)
    IOLoop.instance().start()


def gunicorn_adapter(host, port):
    from gunicorn import version_info
    
    if version_info < (0, 9, 0):
        from gunicorn.arbiter import Arbiter
        from gunicorn.config import Config
        arbiter = Arbiter(Config({'bind': "%s:%d" % (host, int(port)), 'workers': 4}), handle_request)
        arbiter.run()
    else:
        from gunicorn.app.base import Application
        
        class IttyApplication(Application):
            def init(self, parser, opts, args):
                return {
                    'bind': '{0}:{1}'.format(host, port),
                    'workers': 4
                }
            
            def load(self):
                return handle_request
        
        IttyApplication().run()


def gevent_adapter(host, port):
    from gevent import wsgi
    wsgi.WSGIServer((host, int(port)), handle_request).serve_forever()


WSGI_ADAPTERS = {
    'wsgiref': wsgiref_adapter,
    'appengine': appengine_adapter,
    'cherrypy': cherrypy_adapter,
    'flup': flup_adapter,
    'paste': paste_adapter,
    'twisted': twisted_adapter,
    'diesel': diesel_adapter,
    'tornado': tornado_adapter,
    'gunicorn': gunicorn_adapter,
    'gevent': gevent_adapter,
}


# Server

def run_itty(server='wsgiref', host='localhost', port=8080, config=None):
    """
    Runs the itty web server.
    
    Accepts an optional host (string), port (integer), server (string) and
    config (python module name/path as a string) parameters.
    
    By default, uses Python's built-in wsgiref implementation. Specify a server
    name from WSGI_ADAPTERS to use an alternate WSGI server.
    """
    if not server in WSGI_ADAPTERS:
        raise RuntimeError("Server '%s' is not a valid server. Please choose a different server." % server)
    
    if config is not None:
        # We'll let ImportErrors bubble up.
        config_options = __import__(config)
        host = getattr(config_options, 'host', host)
        port = getattr(config_options, 'port', port)
        server = getattr(config_options, 'server', server)
    
    # AppEngine seems to echo everything, even though it shouldn't. Accomodate.
    if server != 'appengine':
        print 'itty starting up (using %s)...' % server
        print 'Listening on http://%s:%s...' % (host, port)
        print 'Use Ctrl-C to quit.'
        print
    
    try:
        WSGI_ADAPTERS[server](host, port)
    except KeyboardInterrupt:
        print 'Shutting down. Have a nice day!'
