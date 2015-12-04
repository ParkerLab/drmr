#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()

requirements = [
    'Jinja2'
]

test_requirements = []

setup(
    name='drmr',
    version='0.1.0',
    description="A tool for submitting pipeline scripts to distributed resource managers.",
    long_description=readme + '\n\n',
    author="The Parker Lab",
    author_email='parkerlab-software@umich.edu',
    url='https://github.com/ParkerLab/drmr',
    packages=['drmr', 'drmr.drm'],
    scripts=[
        'scripts/drmr',
    ],
    include_package_data=True,
    install_requires=requirements,
    license="GPLv3+",
    zip_safe=False,
    keywords='DRM pipeline',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
