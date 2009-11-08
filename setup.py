#!/usr/bin/env python

from distutils.core import setup
import os
from itty import __version__

long_desc = ''

try:
    long_desc = os.path.join(os.path.dirname(__file__), 'README.rst').read()
except:
    # The description isn't worth a failed install...
    pass

classifiers = ['License :: OSI Approved :: BSD License']
setup(
    name='itty',
    version='%s.%s.%s' % __version__,
    description='The itty-bitty Python web framework.',
    long_description=long_desc,
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/itty/',
    py_modules=['itty'],
    license='BSD',
    classifiers=classifiers,
)
