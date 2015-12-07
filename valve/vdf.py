# -*- coding: utf-8 -*-

"""Tools for handling the Valve Data Format (VDF).

This module provides functionality to serialise and deserialise VDF
formatted data using an API similar to that of the built-in :mod:`json`
library.

https://developer.valvesoftware.com/wiki/KeyValues
"""


class VDFDecoder(object):
    """Streaming VDF decoder."""

    def feed(self, fragment):
        pass


class VDFEncoder(object):
    pass


def load(file_, cls=None):
    pass


def loads(vdf, cls=None):
    pass


def dump(object_, file_, cls=None):
    pass


def dumps(object_, cls=None):
    pass
