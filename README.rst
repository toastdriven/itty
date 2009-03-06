=======
itty.py
=======

The itty-bitty Python web framework.

``itty.py`` is a little experiment, an attempt at a Sinatra_ influenced 
micro-framework that does just enough to be useful and nothing more.

This is not even alpha-quality stuff, so beware.


.. _Sinatra: http://sinatrarb.com/


Example
=======

::

  from itty import get, run_itty
  
  @get('/')
  def index():
      return 'Hello World!'
  
  run_itty()

See ``test_itty.py`` for more usage.