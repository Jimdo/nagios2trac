#!/usr/bin/env python

from distutils.core import setup

setup(name='nagios2trac',
      version='0.2.2',
      description='Let Nagios Create or Comment on Trac Tickets',
      author='Daniel Bonkowski',
      author_email='bonko@jimdo.com',
      url='https://github.com/Jimdo/nagios2trac',
      scripts = ['nagios2trac.py'],
     )
