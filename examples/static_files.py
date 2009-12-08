from itty import *

MY_ROOT = os.path.join(os.path.dirname(__file__), 'media')


@get('/')
def index(request):
    return '<img src="media/itty.png">'

# To serve static files, simply setup a standard @get method. You should
# capture the filename/path and get the content-type. If your media root is
# different than where your ``itty.py`` lives, manually setup your root
# directory as well. Finally, use the ``static_file`` helper to serve up the
# file.
@get('/media/(?P<filename>.+)')
def my_media(request, filename):
    output = static_file(filename, root=MY_ROOT)
    return Response(output, content_type=content_type(filename))


# Alternative, if sane-ish defaults are good enough for you, you can use the
# ``serve_static_file`` handler to do the heavy lifting for you. For example:
@get('/simple/')
def simple(request):
    return """
<html>
    <head>
        <title>Simple CSS</title>
        <link rel="stylesheet" type="text/css" href="/simple_media/default.css">
    </head>
    <body>
        <h1>Simple CSS is Simple!</h1>
        <p>Simple reset here.</p>
    </body>
</html>
"""

# By default, the ``serve_static_file`` will try to guess the correct content
# type. If needed, you can enforce a content type by using the
# ``force_content_type`` kwarg (i.e. ``force_content_type='image/jpg'`` on a
# directory of user uploaded images).
@get('/simple_media/(?P<filename>.+)')
def simple_media(request, filename):
    return serve_static_file(request, filename, root=MY_ROOT)


run_itty()
