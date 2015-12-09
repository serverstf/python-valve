# -*- coding: utf-8 -*-

"""Tools for handling the Valve Data Format (VDF).

This module provides functionality to serialise and deserialise VDF
formatted data using an API similar to that of the built-in :mod:`json`
library.

https://developer.valvesoftware.com/wiki/KeyValues
"""

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import abc


class VDFError(Exception):
    """Base exception for all VDF errors."""


class VDFSyntaxError(SyntaxError, VDFError):
    """Exception for VDF syntax errors."""

    def __init__(self, source, line, column, message):
        self.source = source
        self.line = line
        self.column = column
        self.message = message

    def __str__(self):
        return "line {0.line}, column {0.column}: {0.message}".format(self)


class IncludeResolutionError(VDFError):
    """Raised when resolving an include fails."""


class IncludeResolver(abc.ABC):
    """Base class for resolving includes.

    VDF supports includes via ``#include`` and ``#base``. Whenever the
    parser reaches one of these includes it needs to resolve the name
    to VDF fragments which are then parsed.

    You cannot instantiate this class directly. Use one of the concrete
    implementations: :class:`IgnoreIncludeResolver`,
    :class:`DisabledIncludeResolver` or :class:`FileSystemIncludeResolver`.
    """

    @abc.abstractmethod
    def resolve(self, name):
        """Resolve a VDF include to VDF fragments.

        :param str name: the name of the VDF document to include.

        :raises IncludeResolutionError: if the name cannot be resolved.

        :returns: an interator of VDF fragments as strings.
        """


class IgnoreIncludeResolver(IncludeResolver):
    """Include resolver that doesn't actually resolve to anything.

    Specifically, all names resolve to an empty fragment.
    """

    def resolve(self, name):
        yield ""


class DisabledIncludeResolver(IncludeResolver):
    """Disables include resolution.

    Instead this always raises :exc:`IncludeResolutionError` when attempting
    to resolve an include.
    """

    def resolve(self, name):
        raise IncludeResolutionError("Includes are disabled")


class FileSystemIncludeResolver(IncludeResolver):
    """Resolve includes relative to a file-system path.

    :param pathlib.Path path: the base path to resolve includes relative to.
    :param int chunk_size: the number of bytes to read from the file for
        each fragment.
    """

    def __init__(self, path, chunk_size=4096):
        self._path = path
        self._chunk_size = chunk_size

    def resolve(self, name):
        include_path = self._path / name
        try:
            with include_path.open() as include_file:
                for fragment in iter(
                        lambda: include_file.read(self._chunk_size), ""):
                    yield fragment
        except OSError as exc:
            raise IncludeResolutionError(str(exc))


class VDFDecoder(object):
    """Streaming VDF decoder."""

    def __init__(self, includes):
        self._buffer = ""
        self._includes = includes

    def feed(self, fragment):
        pass


class VDFEncoder(object):
    pass


def load(file_):
    pass


def loads(vdf):
    pass


def dump(object_, file_):
    pass


def dumps(object_):
    pass
