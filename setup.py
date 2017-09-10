# -*- coding: utf-8 -*-

import os.path
import sys
import textwrap

import setuptools


install_requires = [
    "docopt>=0.6.2",
    "monotonic",
    "requests>=2.0",
    "six>=1.6",
]
if sys.version_info[0] == 2:
    install_requires.append("enum34>=1.1")


def readme():
    """Load README contents."""
    path = os.path.join(os.path.dirname(__file__), 'README.rst')
    with open(path) as readme:
        return readme.read()


setuptools.setup(
    name="python-valve",
    version="0.2.0",
    description=("Small library implementing "
                 "various parts of Steam's public interfaces"),
    long_description=readme(),
    author="Oliver Ainsworth",
    author_email="ottajay@googlemail.com",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    extras_require={
        "development": [
            "pylint",
        ],
        "test": [
            "mock==1.0.1",
            "pytest>=2.8.0",
            "pytest-capturelog",
            "pytest-cov",
            "pytest-timeout",
        ],
        "docs": [
            "sphinx",
            "sphinx_rtd_theme",
        ],
    },
    license="MIT License",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
