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
        'collective.mathjax',
        'plone.app.contentlisting',
        'plone.app.contenttypes',
        'plone.app.dexterity',
        'plone.app.relationfield',
        'plone.app.registry',
        'plone.app.textfield',
        'plone.app.vocabularies',
        'plone.intelligenttext',
        'plone.memoize',
        'collective.z3cform.datagridfield',
        'collective.transmogrifier',
        'plone.app.transmogrifier',
        'transmogrify.dexterity',  
        'zope.app.component',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
        ],
    },
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
    """,
    include_package_data=True,
    zip_safe=False,
)
