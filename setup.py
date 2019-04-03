# -*- coding: utf-8 -*-

import os.path
import sys
import textwrap

import setuptools


def readme():
    """Load README contents."""
    path = os.path.join(os.path.dirname(__file__), "README.rst")
    with open(path) as readme:
        return readme.read()


def install_requires():
    """Determine installation requirements."""
    requirements = [
        "docopt>=0.6.2",
        "monotonic",
        "requests>=2.0",
        "six>=1.6",
    ]
    if sys.version_info[0] == 2:
        requirements.append("enum34>=1.1")
    return requirements


setuptools.setup(
    name="python-valve",
    version="0.2.1",
    description=("Python implementation for Source servers, RCON, A2S, "
                 "VDF, the Steam Web API and various other Valve products "
                 "and services."),
    long_description=readme(),
    author="Oliver Ainsworth",
    author_email="ottajay@googlemail.com",
    url="https://github.com/serverstf/python-valve",
    packages=setuptools.find_packages(exclude=["tests"]),
    install_requires=install_requires(),
    extras_require={
        "development": [
            "pylint",
        ],
        "test": [
            "mock==1.0.1",
            "pytest>=3.6.0",
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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Games/Entertainment",
    ],
)
