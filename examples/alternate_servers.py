from itty import *

@get('/')
def index(request):
    return 'Hello World!'

run_itty()
# Same as above: run_itty(server='wsgiref')

# Other options:
# run_itty(server='appengine')
# run_itty(server='cherrypy')
# run_itty(server='flup')
# run_itty(server='paste')
# run_itty(server='twisted')
