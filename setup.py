#!/usr/bin/env python
from distutils.core import setup
import os

long_desc = ''

try:
    long_desc = os.path.join(os.path.dirname(__file__), 'README.rst').read()
except:
    # The description isn't worth a failed install...
    pass

setup(
    name='itty',
    version='0.6.7',
    description='The itty-bitty Python web framework.',
    long_description=long_desc,
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/itty/',
    py_modules=['itty'],
    license='BSD',
    classifiers=[
        'License :: OSI Approved :: BSD License'
    ],
)
