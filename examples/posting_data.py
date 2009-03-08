from itty import *

@get('/simple_post')
def simple_post(request):
    return open('example/html/simple_post.html', 'r').read()

@post('/test_post')
def test_post(request):
    return "'foo' is: %s" % request.POST.get('foo', 'not specified')

@get('/complex_post')
def complex_post(request):
    return open('example/html/complex_post.html', 'r').read()

@post('/test_complex_post')
def test_complex_post(request):
    html = """
    'foo' is: %s<br>
    'bar' is: %s
    """ % (request.POST.get('foo', 'not specified'), request.POST.get('bar', 'not specified'))
    return html

run_itty()
