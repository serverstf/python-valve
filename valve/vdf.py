# -*- coding: utf-8 -*-
# Copyright (C) 2013-2017 Oliver Ainsworth

"""Tools for handling the Valve Data Format (VDF).

This module provides functionality to serialise and deserialise VDF
formatted data using an API similar to that of the built-in :mod:`json`
library.

https://developer.valvesoftware.com/wiki/KeyValues
"""

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import abc
import io

import six


class VDFError(Exception):
    """Base exception for all VDF errors."""


class VDFTransclusionError(Exception):
    """Raised for errors transcluding VDF documents."""


@six.add_metaclass(abc.ABCMeta)
class VDFTranscluder:
    """Abstract base class for VDF document transcluders.

    When :class:`VDFDecoder` encounters a ``#base`` transclusion
    directive in a VDF document it will defer loading of the document
    to a configured transcluder.
    """

    @abc.abstractmethod
    def transclude(self, name):
        """Transclude a VDF document by name.

        :param name: The name of the VDF document to be transcluded.
            The exact semantics of the name is dependant on the concrete
            transcluder implementation.
        :type name: str

        :raises VDFTransclusionError: If the requested document cannot
            be transcluded for any reason.

        :returns: An iterator of the transcluded document's contents as
            strings.
        """
        raise NotImplementedError  # pragma: no cover


class VDFIgnoreTranscluder(VDFTranscluder):
    def transclude(self, name): yield ""


class VDFDisabledTranscluder(VDFTranscluder):
    def transclude(self, name): yield ""


class VDFFileSystemTranscluder(VDFTranscluder):
    def __init__(self, buffer_size=4096): pass
    def transclude(self, name): yield ""


class VDFTestTranscluder(VDFTranscluder):
    """VDF transcluder for testing.

    Instances of this transcluder allow documents to be manually
    specified via :meth:`register`. Registered documents can then
    be removed with :meth:`unregister`.
    """

    def __init__(self):
        self._documents = {}

    def register(self, name, document):
        """Register a document.

        :param name: Name of the document to register.
        :type name: str
        :param document: Document contents.
        :type document: str

        :raises LookupError: If the a document with the given name
            has already been registered.
        """
        if name in self._documents:
            raise LookupError(
                "Document with name '{}' already registered".format(name))
        self._documents[name] = document

    def unregister(self, name):
        """Unregister a document.

        :param name: Name of the document to unregister.
        :type name: str

        :raises LookupError: If no document with the given name has
            been registered.
        """
        if name not in self._documents:
            raise LookupError("No document with name '{}'".format(name))
        self._documents.pop(name, None)

    def transclude(self, name):
        if name not in self._documents:
            raise VDFTransclusionError(
                "No document with name '{}'".format(name))
        yield self._documents[name]


class VDFDecoder:

    def __init__(self, transcluder): pass
    def __enter__(self): pass
    def __exit__(self): pass

    def feed(self, fragment): pass
    def complete(self): pass
    def on_object_enter(self): pass
    def on_object_exit(self): pass
    def on_key(self, key): pass
    def on_value(self, value): pass


class VDFObjectDecoder(VDFDecoder):

    def __init__(self, transcluder):
        self.object = {}
        self._key = None
        self._stack = [self.object]

    def on_object_enter(self):
        object_ = {}
        self._stack[-1][self._key] = object_
        self._stack.append(object_)
        self._key = None

    def on_object_exit(self):
        self._stack.pop()

    def on_key(self, key):
        self._key = key

    def on_value(self, value):
        self._stack[-1][self._key] = value
        self._key = None


def load(readable, transcluder=VDFDisabledTranscluder()):
    """Load an object from a VDF file."""
    with VDFObjectDecoder(transcluder) as decoder:
        for chunk in iter(lambda: readable.read(4096), ''):
            decoder.feed(chunk)
    return decoder.object


def loads(vdf, transcluder=VDFDisabledTranscluder()):
    """Load an object from a VDF string."""
    return load(io.StringIO(vdf))


def dump(object_, writable):
    """Serialise an object into a VDF file."""


def dumps(object_):
    """Serialise an object into a VDF string."""
    buffer_ = io.StringIO()
    dump(object_, buffer_, transcluder)
    return buffer_.getvalue()
