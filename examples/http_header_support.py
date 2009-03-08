from itty import *

@get('/ct')
def ct(request):
    ct.content_type = 'text/plain'
    return 'Check your Content-Type headers.'

@get('/headers')
def test_headers(request):
    test_headers.headers = [
        ('X-Powered-By', 'itty'),
        ('Set-Cookie', 'username=daniel')
    ]
    return 'Check your headers.'

@get('/test_redirect')
def test_redirect(request):
    raise Redirect('/hello')

run_itty()
