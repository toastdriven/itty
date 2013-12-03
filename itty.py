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
import base64
import cgi
import datetime
import hashlib
import hmac
import logging
import mimetypes
import numbers
import os
import re
import StringIO
import sys
import time
import traceback
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs
try:
    import Cookie
except ImportError:
    import http.cookies as Cookie

__author__ = 'Daniel Lindsley'
__version__ = ('0', '8', '2')
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

if hasattr(hmac, 'compare_digest'):  # python 3.3
    _time_independent_equals = hmac.compare_digest
else:
    def _time_independent_equals(a, b):
        if len(a) != len(b):
            return False
        result = 0
        if isinstance(a[0], int):  # python3 byte strings
            for x, y in zip(a, b):
                result |= x ^ y
        else:  # python2
            for x, y in zip(a, b):
                result |= ord(x) ^ ord(y)
        return result == 0

if type('') is not type(b''):
    def u(s):
        return s
    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring

_UTF8_TYPES = (bytes_type, type(None))


def utf8(value):
    """Converts a string argument to a byte string.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    assert isinstance(value, unicode_type)
    return value.encode("utf-8")

_TO_UNICODE_TYPES = (unicode_type, type(None))


def to_unicode(value):
    """Converts a string argument to a unicode string.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    assert isinstance(value, bytes_type)
    return value.decode("utf-8")

_unicode = to_unicode

if str is unicode_type:
    native_str = to_unicode
else:
    native_str = utf8


def format_timestamp(ts):
    """Formats a timestamp in the format used by HTTP.
    """
    if isinstance(ts, (tuple, time.struct_time)):
        pass
    elif isinstance(ts, datetime.datetime):
        ts = ts.utctimetuple()
    elif isinstance(ts, numbers.Real):
        ts = time.gmtime(ts)
    else:
        raise TypeError("unknown timestamp type: %r" % ts)
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", ts)


def create_signed_value(secret, name, value):
    timestamp = utf8(str(int(time.time())))
    value = base64.b64encode(utf8(value))
    signature = _create_signature(secret, name, value, timestamp)
    value = b"|".join([value, timestamp, signature])
    return value


def decode_signed_value(secret, name, value, max_age_days=31):
    if not value:
        return None
    parts = utf8(value).split(b"|")
    if len(parts) != 3:
        return None
    signature = _create_signature(secret, name, parts[0], parts[1])
    if not _time_independent_equals(parts[2], signature):
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - max_age_days * 86400:
        logging.warning("Expired cookie %r", value)
        return None
    if timestamp > time.time() + 31 * 86400:
        # _cookie_signature does not hash a delimiter between the
        # parts of the cookie, so an attacker could transfer trailing
        # digits from the payload to the timestamp without altering the
        # signature.  For backwards compatibility, sanity-check timestamp
        # here instead of modifying _cookie_signature.
        logging.warning("Cookie timestamp in future; possible tampering %r", value)
        return None
    if parts[1].startswith(b"0"):
        logging.warning("Tampered cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0])
    except Exception:
        return None


def _create_signature(secret, *parts):
    hash = hmac.new(utf8(secret), digestmod=hashlib.sha1)
    for part in parts:
        hash.update(utf8(part))
    return utf8(hash.hexdigest())


class HTTPHeaders(dict):
    """A dictionary that maintains Http-Header-Case for all keys.
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._as_list = {}
        self._last_key = None
        if (len(args) == 1 and len(kwargs) == 0 and
                isinstance(args[0], HTTPHeaders)):
            for k, v in args[0].get_all():
                self.add(k, v)
        else:
            self.update(*args, **kwargs)

    def add(self, name, value):
        """Adds a new value for the given key."""
        norm_name = HTTPHeaders._normalize_name(name)
        self._last_key = norm_name
        if norm_name in self:
            dict.__setitem__(self, norm_name,
                             native_str(self[norm_name]) + ',' +
                             native_str(value))
            self._as_list[norm_name].append(value)
        else:
            self[norm_name] = value

    def get_list(self, name):
        """Returns all values for the given header as a list."""
        norm_name = HTTPHeaders._normalize_name(name)
        return self._as_list.get(norm_name, [])

    def get_all(self):
        """Returns an iterable of all (name, value) pairs.

        If a header has multiple values, multiple pairs will be
        returned with the same name.
        """
        for name, list in self._as_list.items():
            for value in list:
                yield (name, value)

    def parse_line(self, line):
        """Updates the dictionary with a single header line.
        """
        if line[0].isspace():
            # continuation of a multi-line header
            new_part = ' ' + line.lstrip()
            self._as_list[self._last_key][-1] += new_part
            dict.__setitem__(self, self._last_key,
                             self[self._last_key] + new_part)
        else:
            name, value = line.split(":", 1)
            self.add(name, value.strip())

    @classmethod
    def parse(cls, headers):
        """Returns a dictionary from HTTP header text.
        """
        h = cls()
        for line in headers.splitlines():
            if line:
                h.parse_line(line)
        return h

    def __setitem__(self, name, value):
        norm_name = HTTPHeaders._normalize_name(name)
        dict.__setitem__(self, norm_name, value)
        self._as_list[norm_name] = [value]

    def __getitem__(self, name):
        return dict.__getitem__(self, HTTPHeaders._normalize_name(name))

    def __delitem__(self, name):
        norm_name = HTTPHeaders._normalize_name(name)
        dict.__delitem__(self, norm_name)
        del self._as_list[norm_name]

    def __contains__(self, name):
        norm_name = HTTPHeaders._normalize_name(name)
        return dict.__contains__(self, norm_name)

    def get(self, name, default=None):
        return dict.get(self, HTTPHeaders._normalize_name(name), default)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def copy(self):
        return HTTPHeaders(self)

    _NORMALIZED_HEADER_RE = re.compile(
        r'^[A-Z0-9][a-z0-9]*(-[A-Z0-9][a-z0-9]*)*$')
    _normalized_headers = {}

    @staticmethod
    def _normalize_name(name):
        """Converts a name to Http-Header-Case.
        """
        try:
            return HTTPHeaders._normalized_headers[name]
        except KeyError:
            if HTTPHeaders._NORMALIZED_HEADER_RE.match(name):
                normalized = name
            else:
                normalized = "-".join(
                    [w.capitalize() for w in name.split("-")])
            HTTPHeaders._normalized_headers[name] = normalized
            return normalized


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
        self.headers = HTTPHeaders()
        if self._environ.get("CONTENT_TYPE"):
            self.headers["Content-Type"] = self._environ["CONTENT_TYPE"]
        if self._environ.get("CONTENT_LENGTH"):
            self.headers["Content-Length"] = self._environ["CONTENT_LENGTH"]
        for key in self._environ:
            if key.startswith("HTTP_"):
                self.headers[key[5:].replace("_", "-")] = self._environ[key]
        try:
            self.content_length = int(self._environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            pass

        self.GET = self.build_get_dict()

    def __getattr__(self, name):
        """
        Allow accesses of the environment if we don't already have an attribute
        for. This lets you do things like::

            script_name = request.SCRIPT_NAME
        """
        return self._environ[name]

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

    @property
    def cookies(self):
        """A dictionary of Cookie.Morsel objects."""
        if not hasattr(self, "_cookies"):
            self._cookies = Cookie.SimpleCookie()
            if "Cookie" in self.headers:
                try:
                    self._cookies.load(
                        native_str(self.headers["Cookie"]))
                except Exception:
                    self._cookies = None
        return self._cookies

    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default."""
        if self.cookies is not None and name in self.cookies:
            return self.cookies[name].value
        return default

    def get_secure_cookie(self, name, value=None, max_age_days=31):
        """Returns the given signed cookie if it validates, or None.
        """
        if value is None:
            value = self.get_cookie(name)
        return decode_signed_value(COOKIE_SECRET, name, value,
                                   max_age_days=max_age_days)

    def build_get_dict(self):
        """Takes GET data and rips it apart into a dict."""
        raw_query_dict = parse_qs(self.query, keep_blank_values=1)
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

    def __init__(self, output, headers=None, status=200, content_type='text/html'):
        self.output = output
        self.content_type = content_type
        self.status = status
        self.headers = HTTPHeaders()

        if headers and isinstance(headers, HTTPHeaders):
            self.headers = headers
        if headers and isinstance(headers, list):
            for (key, value) in headers:
                self.headers.add(key, value)

    def add_header(self, key, value):
        self.headers.add(key, value)

    def set_cookie(self, name, value, domain=None, expires=None, path="/",
                   expires_days=None, **kwargs):
        """Sets the given cookie name/value with the given options.
        """
        name = native_str(name)
        value = native_str(value)
        if re.search(r"[\x00-\x20]", name + value):
            raise ValueError("Invalid cookie %r: %r" % (name, value))
        if not hasattr(self, "_new_cookie"):
            self._new_cookie = Cookie.SimpleCookie()
        if name in self._new_cookie:
            del self._new_cookie[name]
        self._new_cookie[name] = value
        morsel = self._new_cookie[name]
        if domain:
            morsel["domain"] = domain
        if expires_days is not None and not expires:
            expires = datetime.datetime.utcnow() + datetime.timedelta(
                days=expires_days)
        if expires:
            morsel["expires"] = format_timestamp(expires)
        if path:
            morsel["path"] = path
        for k, v in kwargs.items():
            if k == 'max_age':
                k = 'max-age'
            morsel[k] = v

    def clear_cookie(self, name, path="/", domain=None):
        """Deletes the cookie with the given name."""
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        self.set_cookie(name, value="", path=path, expires=expires,
                        domain=domain)

    def clear_all_cookies(self):
        """Deletes all the cookies the user sent with this request."""
        for name in self.request.cookies:
            self.clear_cookie(name)

    def set_secure_cookie(self, name, value, expires_days=30, **kwargs):
        """Signs and timestamps a cookie so it cannot be forged."""
        self.set_cookie(name, self.create_signed_value(name, value),
                        expires_days=expires_days, **kwargs)

    def create_signed_value(self, name, value):
        """Signs and timestamps a string so it cannot be forged.
        """
        return create_signed_value(COOKIE_SECRET, name, value)

    def send(self, start_response):
        status = "%d %s" % (self.status, HTTP_MAPPINGS.get(self.status))
        headers = ([('Content-Type', "%s; charset=utf-8" % self.content_type)] +
                  [(k, v) for k, v in self.headers.iteritems()])

        if hasattr(self, "_new_cookie"):
            for cookie in self._new_cookie.values():
                headers.append(("Set-Cookie", utf8(cookie.OutputString(None))))

        start_response(status, headers)

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
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['GET'].append((re_url, url, method))
        return method
    return wrapped


def post(url):
    """Registers a method as capable of processing POST requests."""
    def wrapped(method):
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['POST'].append((re_url, url, method))
        return method
    return wrapped


def put(url):
    """Registers a method as capable of processing PUT requests."""
    def wrapped(method):
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['PUT'].append((re_url, url, method))
        new.status = 201
        return method
    return wrapped


def delete(url):
    """Registers a method as capable of processing DELETE requests."""
    def wrapped(method):
        # Register.
        re_url = re.compile("^%s$" % add_slash(url))
        REQUEST_MAPPINGS['DELETE'].append((re_url, url, method))
        return method
    return wrapped


def error(code):
    """Registers a method for processing errors of a certain HTTP code."""
    def wrapped(method):
        # Register.
        ERROR_HANDLERS[code] = method
        return method
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
    from gevent import pywsgi
    pywsgi.WSGIServer((host, int(port)), handle_request).serve_forever()


def eventlet_adapter(host, port):
    from eventlet import wsgi, listen
    wsgi.server(listen((host, int(port))), handle_request)


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
    'eventlet': eventlet_adapter,
}


COOKIE_SECRET = None

# Server


def run_itty(server='wsgiref', host='localhost', port=8080, config=None,
    cookie_secret=None):
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

    global COOKIE_SECRET
    COOKIE_SECRET = cookie_secret or base64.b64encode(os.urandom(32))

    try:
        WSGI_ADAPTERS[server](host, port)
    except KeyboardInterrupt:
        print 'Shutting down. Have a nice day!'
