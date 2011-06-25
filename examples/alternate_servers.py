from itty import *

@get('/')
def index(request):
    return 'Hello World!'

run_itty()
# Same as above: run_itty(server='wsgiref')

# Other options:
# run_itty(server='tornado')
# run_itty(server='diesel')
# run_itty(server='twisted')
# run_itty(server='appengine')
# run_itty(server='cherrypy')
# run_itty(server='flup')
# run_itty(server='paste')
# run_itty(server='gunicorn')
# run_itty(server='gevent')
# run_itty(server='eventlet')
