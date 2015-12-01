# -*- coding: utf-8 -*-

import sys
import textwrap

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


install_requires = [
    "six>=1.6",
    "requests>=2.0",
]
if sys.version_info[0] == 2:
    install_requires.append("enum34>=1.1")


class PyTest(TestCommand):
    # http://pytest.org/latest/goodpractises.html#integration-with-setuptools-test-commands

    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Import here, cause outside the eggs aren't loaded
        import pytest
        sys.exit(pytest.main(self.pytest_args))


setup(
    name="python-valve",
    version="0.1.1",
    description=("Small library implementing "
                 "various parts of Steam's public interfaces"),
    author="Oliver Ainsworth",
    author_email="ottajay@googlemail.com",
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=[
        "pytest",
        "mock==1.0.1",
    ],
    extras_require={
        "development": [
            "pylint",
        ],
    },
    license="MIT License",
    cmdclass={
        "test": PyTest,
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
    ],
)
