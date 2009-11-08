from itty import *

# Your application code.
@get('/')
def hello(request):
    return 'Hello World!'

# The hook to make it run in a mod_wsgi environment.
def application(environ, start_response):
    return handle_request(environ, start_response)
