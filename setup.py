#!/usr/bin/env python

from setuptools import setup

setup(name='velogames_scraper',
      version='0.1',
      description='Api and scraper for velogames website.',
      author='Jonathan Villemaire-Krajden',
      author_email='odontomachus@gmail.com',
      install_requires = [
          'tornado',
          'lxml',
        ]
     )
