#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='paragraphica',
    version="0.0",
    description='The SBP implementation of Paragraphica',
    long_description=long_description,
    license='MIT',
    author='Bjoern Karmann',
    # author_email='',
    maintainer='Marco Schreurs, Ilja Heitlager',
    maintainer_email='mschreurs@schubergphilis.com, iheitlager@schubergphilis.com',
    keywords=["hack interpreter", "development-tools"],
    url='https://github.com/lab271/demo-paragraphica',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    test_suite="tests",
    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.11",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English"
    ],
    install_requires=[],
    zip_safe=True,
)
