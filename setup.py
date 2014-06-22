# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Oliver Ainsworth

from setuptools import setup

setup(
    name="python-valve",
    version="0.0",
    description="Small library implementing various parts of Steam's public interfaces",
    author="Oliver Ainsworth",
    author_email="ottajay@googlemail.com",
    packages=["valve", "valve.steam", "valve.source"],
    install_requires=[
        "six>=1.6",
        "requests>=2.0",
    ],
    license="MIT License",
)
