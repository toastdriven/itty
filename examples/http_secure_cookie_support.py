# -*- coding: utf-8 *-*
from itty import *

@get('/receive')
def receive_cookies(request):
    response = Response(str(request.get_secure_cookie('foo')),
                        content_type='text/plain')
    return response

@get('/send')
def response_cookies(request):
    response = Response('Check your cookies.')
    response.set_secure_cookie('foo', 'bar')
    return response

run_itty(cookie_secret='MySeCrEtCoOkIe')
