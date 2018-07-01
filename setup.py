#!/usr/bin/env python3
#

import setuptools

import gedcom

setuptools.setup(
    name='gedcom',
    version=gedcom.version,
    description='GEDCOM processing stuff',
    long_description=open('README.rst').read(),
    author='Dave Shawley',
    author_email='daveshawley@gmail.com',
    url='https://github.com/dave-shawley/gedcom',
    packages=['gedcom'],
    install_requires=['tqdm==4.23.4'],
    extras_require={
        'dev': [
            'coverage==4.5.1',
            'flake8==3.5.0',
            'nose==1.3.7',
            'sphinx==1.7.5',
            'yapf==0.22.0',
        ],
    },
)
