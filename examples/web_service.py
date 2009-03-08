from itty import *

@get('/get/(?P<name>\w+)')
def test_get(request, name=', world'):
    return 'Hello %s!' % name

@post('/post')
def test_post(request):
    return "'foo' is: %s" % request.POST.get('foo', 'not specified')

@put('/put')
def test_put(request):
    return "'foo' is: %s" % request.PUT.get('foo', 'not specified')

@delete('/delete')
def test_delete(request):
    return 'Method received was %s.' % request.method

run_itty()
