# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


class APIObjectsIterator(object):

    def __init__(self, cls, arguments=[]):
        self.cls = cls
        self.arguments = arguments

    def __iter__(self):

        def generator():
            for args, kwargs in self.arguments:
                yield self.cls(*args, **kwargs)

        return generator()

    def __repr__(self):
        return "<iterator of {} '{}.{}' objects>".format(
            len(self.arguments), self.cls.__module__, self.cls.__name__)
