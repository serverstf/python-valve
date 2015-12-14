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

import six


class VDFError(Exception):
    """Base exception for all VDF errors."""


class VDFSyntaxError(SyntaxError, VDFError):
    """Exception for VDF syntax errors."""

    def __init__(self, line, column, message):
        self.line = line
        self.column = column
        self.message = message

    def __str__(self):
        return "line {0.line}, column {0.column}: {0.message}".format(self)


class IncludeResolutionError(VDFError):
    """Raised when resolving an include fails."""


@six.add_metaclass(abc.ABCMeta)
class IncludeResolver(object):
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

    _CURLY_LEFT_BRACKET = "{"
    _CURLY_RIGHT_BRACKET = "}"
    _LINE_FEED = "\n"
    _QUOTATION_MARK = "\""
    _REVERSE_SOLIDUS = "\\"
    _WHITESPACE = [" ", "\t"]
    _ESCAPE_SEQUENCES = {
        "n": "\n",
        "t": "\t",
        "\\": "\\",
        "\"": "\"",
    }

    def __init__(self, includes):
        self._line = 1
        self._column = 0
        self._includes = includes
        self._parser = self._parse_whitespace()
        next(self._parser)
        self.object = {}
        self._active_object = self.object
        self._key = ""
        self._value = None

    def _parse_whitespace(self):
        while True:
            character = yield
            if character not in self._WHITESPACE:
                return

    def _parse_key(self):
        key = ""
        first_character = yield
        if first_character == self._QUOTATION_MARK:
            quoted = True
        else:
            quoted = False
        escape = False
        while True:
            character = yield
            if not escape and character == self._QUOTATION_MARK:
                yield  # Consume trailing quotation mark
                break
            if character == self._REVERSE_SOLIDUS:
                escape = True
                continue
            if escape:
                if character in self._ESCAPE_SEQUENCES:
                    character = self._ESCAPE_SEQUENCES[character]
                    escape = False
                else:
                    raise SyntaxError(
                        "Invalid escape sequence '\\{}'".format(character))
            key += character
        self._key = key

    def _next_parser(self, previous):
        if self._key:
            return self._parse_whitespace()
        else:
            return self._parse_key()

    def feed(self, fragment):
        while fragment:
            character, fragment = fragment[0], fragment[1:]
            self._column += 1
            if character == self._LINE_FEED:
                self._line += 1
                self._column = 1
            try:
                self._parser.send(character)
            except StopIteration:
                fragment = character + fragment
                self._parser = self._next_parser(self._parser)
                next(self._parser)
            except SyntaxError as exc:
                raise VDFSyntaxError(self._line, self._column, str(exc))


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
