from itty import get, post, run_itty

@get('/')
def index():
    return 'Indexed!'

@get('/hello')
def greeting():
    return 'Hello World!'

@get('/hello/(?P<name>\w+)')
def personal_greeting(name=', world'):
    return 'Hello %s!' % name

run_itty()
