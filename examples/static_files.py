from itty import *

# By default, itty can serve static media out of the ``media`` folder for all
# requests coming from ``/media``.

# So in your browser, you should be able to hit ``/media/default.css`` or
# ``/media/itty.png``.

# If you uncomment the below, you can manipulate both the path and the url into
# whatever you choose.

# import os
# Media.path = '/public'
# Media.root = os.path.join(os.path.dirname(__file__), 'html')

@get('/')
def index(request):
    return 'Hello World!'

run_itty()
