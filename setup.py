#!/usr/bin/env python

from setuptools import Command
from distutils.core import setup
import sys


class PyPandoc(Command):
    description = 'Generates the documentation in reStructuredText format.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def convert(self, infile, outfile):
        import pypandoc
        with open(outfile, 'w+') as f:
            f.write(pypandoc.convert(infile, 'rst'))

    def run(self):
        self.convert('README.md', 'rst/README.rst')
        self.convert('CHANGELOG.md', 'rst/CHANGELOG.rst')

setup(name='nagios2trac',
      version='0.5',
      description='Let Nagios Create or Comment on Trac Tickets',
      long_description=open('rst/README.rst').read() + '\n\n' +
                       open('rst/CHANGELOG.rst').read(),
      author='Daniel Bonkowski',
      author_email='bonko@jimdo.com',
      url='https://github.com/Jimdo/nagios2trac',
      license='Apache',
      scripts=['nagios2trac.py'],
      cmdclass={'doc': PyPandoc}
      )
