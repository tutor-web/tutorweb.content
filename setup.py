# -*- coding: utf-8 -*-

import os

from setuptools import setup
from setuptools import find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name='tutorweb.content',
    version='0.1.dev0',
    description='Tutorweb content module',
    long_description=read('README.rst') +
                     read('HISTORY.rst'),
    classifiers=[
        "Programming Language :: Python",
    ],
    keywords='plone tutorweb',
    author='Jamie Lentin',
    author_email='lentinj@shuttlethread.com',
    url='https://github.com/tutorweb/tutorweb.content',
    license='GPL',
    packages=find_packages(),
    namespace_packages=['tutorweb'],
    install_requires=[
        'setuptools',
        'plone.subrequest',
        'Products.TutorWeb',
        'lxml',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
        ],
    },
    entry_points="""
    """,
    include_package_data=True,
    zip_safe=False,
)
