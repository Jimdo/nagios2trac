#!/usr/bin/env python

from distutils.core import setup

setup(name='nagios2trac',
      version='0.4',
      description='Let Nagios Create or Comment on Trac Tickets',
      author='Daniel Bonkowski',
      author_email='bonko@jimdo.com',
      url='https://github.com/Jimdo/nagios2trac',
      license='Apache',
      scripts=['nagios2trac.py'],
      )
