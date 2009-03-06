from itty import get, post, run_itty

@get('/')
def index(request):
    return 'Indexed!'

@get('/hello')
def greeting(request):
    return 'Hello World!'

@get('/hello/(?P<name>\w+)')
def personal_greeting(request, name=', world'):
    return 'Hello %s!' % name

@get('/ct')
def ct(request):
    ct.content_type = 'text/plain'
    return 'Check your Content-Type headers.'

run_itty()
