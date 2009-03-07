from itty import *

@error(500)
def my_great_500(exception, env, start_response):
    start_response('500 APPLICATION ERROR', [('Content-Type', 'text/html')])
    html_output = """
    <html>
        <head>
            <title>Application Error! OH NOES!</title>
        </head>
        
        <body>
            <h1>OH NOES!</h1>
            
            <p>Yep, you broke it.</p>
            
            <p>Exception: %s</p>
        </body>
    </html>
    """ % exception.args
    return [html_output]

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

@get('/test_404')
def test_404(request):
    raise NotFound('Not here, sorry.')
    return 'This should never happen.'

@get('/test_500')
def test_500(request):
    raise RuntimeError('Oops.')
    return 'This should never happen either.'

@get('/test_redirect')
def test_redirect(request):
    raise Redirect('/hello')

run_itty()
