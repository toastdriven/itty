from itty import *

@get('/test_500')
def test_500(request):
    raise RuntimeError('Oops.')
    return 'This should never happen either.'

run_itty()
