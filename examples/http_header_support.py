# -*- coding: utf-8 -*-
from itty import *

@get('/ct')
def ct(request):
    response = Response('Check your Content-Type headers.', content_type='text/plain')
    return response

@get('/headers')
def test_headers(request):
    headers = [
        ('X-Powered-By', 'itty'),
        ('Set-Cookie', 'username=daniel')
    ]
    response = Response('Check your headers.', headers=headers)
    return response

@get('/redirected')
def index(request):
    return 'You got redirected!'

@get('/test_redirect')
def test_redirect(request):
    raise Redirect('/redirected')

@get('/unicode')
def unicode(request):
    return u'Works with Unîcødé too!'

run_itty()
