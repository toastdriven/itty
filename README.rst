=======
itty.py
=======

The itty-bitty Python web framework.

``itty.py`` is a little experiment, an attempt at a Sinatra_ influenced 
micro-framework that does just enough to be useful and nothing more.

Currently supports:

* Routing
* Basic responses
* Content-types
* HTTP Status codes
* URL Parameters
* Basic GET/POST/PUT/DELETE support
* User-definable error handlers

This is not even alpha-quality stuff, so beware. It's also a lot of fun.

.. _Sinatra: http://sinatrarb.com/


Example
=======

::

  from itty import get, run_itty
  
  @get('/')
  def index():
      return 'Hello World!'
  
  run_itty()

See ``test/test_itty.py`` for more usage.