from itty import *

@get('/')
def index(request):
    return 'Hello World!'

# To serve static files, simply setup a standard @get method. You should
# capture the filename/path and get the content-type. If your media root is
# different than where your ``itty.py`` lives, manually setup your root
# directory as well. Finally, use the ``static_file`` handler to serve up the
# file.
@get('/media/(?P<filename>.+)')
def my_media(request, filename):
    my_media.content_type = content_type(filename)
    my_root = os.path.join(os.path.dirname(__file__), 'media')
    return static_file(request, filename=filename, root=my_root)

run_itty()
