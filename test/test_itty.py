from itty import get, post, put, delete, run_itty

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

@get('/test_get')
def test_get(request):
    return "'foo' is: %s" % request.GET.get('foo', 'not specified')

@get('/simple_post')
def simple_post(request):
    return open('simple_post.html', 'r').read()

@post('/test_post')
def test_post(request):
    return "'foo' is: %s" % request.POST.get('foo', 'not specified')

@put('/test_put')
def test_put(request):
    return "'foo' is: %s" % request.PUT.get('foo', 'not specified')

@delete('/test_delete')
def test_delete(request):
    return 'Method received was %s.' % request.method

run_itty()
