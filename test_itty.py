from itty import get, post, run_itty

@get('/')
def index():
    return 'Indexed!'

@get('/hello')
def greeting():
    return 'Hello World!'

run_itty()
