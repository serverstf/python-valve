# -*- coding: utf-8 -*-

import sys
import textwrap

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


install_requires = [
    "docopt>=0.6.2",
    "monotonic",
    "requests>=2.0",
    "six>=1.6",
]
if sys.version_info[0] == 2:
    install_requires.append("enum34>=1.1")


setup(
    name="python-valve",
    version="0.1.1",
    description=("Small library implementing "
                 "various parts of Steam's public interfaces"),
    author="Oliver Ainsworth",
    author_email="ottajay@googlemail.com",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        "development": [
            "pylint",
        ],
        "test": [
            "mock==1.0.1",
            "pytest>=2.8.0",
            "pytest-capturelog",
            "pytest-timeout",
        ],
    },
    license="MIT License",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
    ],
)
