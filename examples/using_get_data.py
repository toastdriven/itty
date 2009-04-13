from itty import *

@get('/')
def test_get(request):
    return "'foo' is: %s" % request.GET.get('foo', 'not specified')

run_itty()
