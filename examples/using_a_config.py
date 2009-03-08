from itty import *

@get('/')
def index(request):
    return 'Hello World!'

run_itty(config='sample_conf')
