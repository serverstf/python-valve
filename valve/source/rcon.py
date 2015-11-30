# -*- coding: utf-8 -*-

"""Source Dedicated Server remote console (RCON) interface."""

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import enum
import logging
import socket


log = logging.getLogger(__name__)


class RCONError(Exception):
    """Base exception for all RCON-related errors."""


class RCONCommunicationError(RCONError):
    """Used for propagating socket-related errors."""


class RCONTimeoutError(RCONError):
    """Raised when a timeout occurs waiting for a response."""


class RCONAuthenticationError(RCONError):
    """Raised for failed authentication."""


class RCONMessageError(RCONError):
    """Raised for errors encoding or decoding RCON messages."""


class RCONMessage(object):
    """Represents a RCON request or response."""

    ENCODING = "ascii"

    class Type(enum.IntEnum):
        """Message types corresponding to ``SERVERDATA_`` constants."""

        RESPONSE_VALUE = 0
        AUTH_RESPONSE = 2
        EXECCOMMAND = 2
        AUTH = 3

    def __init__(self, id_, type_, body_or_text):
        self.id = id_
        self.type = self.Type(type_)
        if isinstance(body_or_text, bytes):
            self.body = body_or_text
        else:
            self.body = b""
            self.text = body_or_text

    @property
    def text(self):
        """Get the body of the message as Unicode.

        :raises UnicodeDecodeError: if the body cannot be decoded as ASCII.

        :returns: the body of the message as a Unicode string.

        .. note::
            It has been reported that some servers may not return valid
            ASCII as they're documented to do so. Therefore you should
            always handle the potential :exc:`UnicodeDecodeError`.

            If the correct encoding is known you can manually decode
            :attr:`body` for your self.
        """
        return self.body.decode(self.ENCODING)

    @text.setter
    def text(self, text):
        """Set the body of the message as Unicode.

        This will attempt to encode the given text as ASCII and set it as the
        body of the message.

        :param str text: the Unicode string to set the body as.

        :raises UnicodeEncodeError: if the string cannot be encoded as ASCII.
        """
        self.body = text.encode(self.ENCODING)

    def encode(self):
        """Encode message to a bytestring."""

    @classmethod
    def decode(self, buffer_):
        """Decode a message from a bytestring.

        This will attempt to decode a single message from the start of the
        given buffer. If the buffer contains more than a single message then
        this must be called multiple times.

        :raises MessageError: if the buffer doesn't contain a valid message.

        :returns: a tuple containing the decoded :class:`RCONMessage` and
            the remnants of the buffer. If the buffer contained exactly one
            message then the remaning buffer will be empty.
        """


class _ResponseBuffer(object):
    """Utility class to buffer RCON responses."""

    def __init__(self):
        self._buffer = b""
        self._responses = []
        self._discard_next = 0

    def _consume(self):
        """Attempt to parse buffer into responses.

        This may or may not consume part of the whole of the buffer.
        """
        while self._buffer:
            try:
                message, self._buffer = RCONMessage.decode(self._buffer)
            except RCONMessageError:
                return
            else:
                self._responses.append(message)

    def feed(self, bytes_):
        """Feed bytes into the buffer."""
        self._buffer += bytes_
        self._consume()

    def discard(self):
        """Discard the next message in the buffer.

        If there are already responses in the buffer then the leftmost
        one will be dropped from the buffer. However, if there's no
        responses currently in the buffer, as soon as one is received it
        will be immediately dropped.

        This can be called multiple times to discard multiple responses.
        """
        if self._responses:
            self._responses.pop(0)
        else:
            self._discard_next += 1


class RCON(object):
    """Represents a RCON connection."""

    def __init__(self, address, password, timeout=None):
        self._address = address
        self._password = password
        self._timeout = timeout
        self._socket = None
        self._closed = False
        self._responses = _ResponseBuffer()

    def __enter__(self):
        self.connect()
        self.authenticate()
        return self

    def __exit__(self, value, type_, traceback):
        self.close()

    def __call__(self, command):
        """Invoke a command.

        This is higher-level version of :meth:`execute`.

        :returns: the response to the command as a Unicode string.
        """

    def connect(self):
        """Create a connection to a server.

        :raises RCONError: if the connection has already been made.
        """
        if self._closed or self._socket:
            raise RCONError("Cannot connect after closing previous "
                            "connection or whilst already connected")
        log.debug("Connecting to %s", self._address)
        self._socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self._socket.connect(self._address)

    def authenticate(self):
        """Authenticate with the server."""

    def close(self):
        """Close connection to a server.

        :raises RCONError: if the connection has not yet been made.
        """
        if not self._socket:
            raise RCONError(
                "Cannot close connection that hasn't been created yet")
        self._closed = True
        self._socket.close()

    def execute(self, command, block=True):
        """Invoke a command.

        Invokes the given command on the conncted server. By default this
        will block (up to the timeout) for a response. This can be disabled
        if you don't care about the response.

        :param bool block: whether or not to wait for a response.

        :raises RCONTimeoutError: if the timeout is reached waiting for a
            response.

        :returns: the response to the command as a :class:`RCONMessage` or
            ``None`` depending on whether ``block`` was ``True`` or not.
        """


def shell(rcon=None):
    """A simple interactive RCON shell.

    An existing, connected and authenticated :class:`RCON` object can be
    given otherwise the shell will prompt for connection details.

    Once connected the shell simply dispatches commands and prints the
    response to stdout.

    :param rcon: the :class:`RCON` object to use for issuing commands
        or ``None``.
    """
