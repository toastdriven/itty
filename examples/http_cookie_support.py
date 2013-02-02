# -*- coding: utf-8 *-*
from itty import *

@get('/receive')
def receive_cookies(request):
    response = Response(repr(request.cookies), content_type='text/plain')
    return response

@get('/send')
def response_cookies(request):
    response = Response('Check your cookies.')
    response.set_cookie('foo', 'bar')
    response.set_cookie('session', 'asdfjlasdfjsdfkjgsdfogd')
    return response

run_itty()
