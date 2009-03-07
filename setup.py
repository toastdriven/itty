#!/usr/bin/env python

from distutils.core import setup
from itty import __version__

classifiers = ['License :: OSI Approved :: MIT License']
setup(name='itty',
      version='%s.%s.%s' % __version__,
      description='The itty-bitty Python web framework.',
      long_description=open('README.rst').read(),
      author='Daniel Lindsley',
      author_email='daniel@toastdriven.com',
      url='http://github.com/toastdriven/itty/',
      py_modules=['itty'],
      license='MIT',
      classifiers=classifiers,
     )
