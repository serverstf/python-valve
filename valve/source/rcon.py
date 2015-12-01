# -*- coding: utf-8 -*-

"""Source Dedicated Server remote console (RCON) interface."""

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import enum
import errno
import logging
import socket
import struct
import time


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

    def __repr__(self):
        return ("<{0.__class__.__name__} "
                "{0.id} {0.type.name} {1}B>").format(self, len(self.body))

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
        terminated_body = self.body + b"\x00\x00"
        size = struct.calcsize("<ii") + len(terminated_body)
        return struct.pack("<iii", size, self.id, self.type) + terminated_body

    @classmethod
    def decode(cls, buffer_):
        """Decode a message from a bytestring.

        This will attempt to decode a single message from the start of the
        given buffer. If the buffer contains more than a single message then
        this must be called multiple times.

        :raises MessageError: if the buffer doesn't contain a valid message.

        :returns: a tuple containing the decoded :class:`RCONMessage` and
            the remnants of the buffer. If the buffer contained exactly one
            message then the remaning buffer will be empty.
        """
        size_field_length = struct.calcsize("<i")
        if len(buffer_) < size_field_length:
            raise RCONMessageError(
                "Need at least {} bytes; got "
                "{}".format(size_field_length, len(buffer_)))
        size_field, raw_message = \
            buffer_[:size_field_length], buffer_[size_field_length:]
        size = struct.unpack("<i", size_field)[0]
        if len(raw_message) < size:
            raise RCONMessageError(
                "Message is {} bytes long "
                "but got {}".format(size, len(raw_message)))
        message, remainder = raw_message[:size], raw_message[size:]
        fixed_fields_size = struct.calcsize("<ii")
        fixed_fields, body_and_terminators = \
            message[:fixed_fields_size], message[fixed_fields_size:]
        id_, type_ = struct.unpack("<ii", fixed_fields)
        body = body_and_terminators[:-2]
        return cls(id_, type_, body), remainder


class _ResponseBuffer(object):
    """Utility class to buffer RCON responses."""

    def __init__(self):
        self._buffer = b""
        self._responses = []
        self._discard_next = 0

    def pop(self):
        """Pop first received message from the buffer.

        :raises RCONError: if there are no whole complete in the buffer.

        :returns: the oldest response in the buffer as a :class:`RCONMessage`.
        """
        if not self._responses:
            raise RCONError("Response buffer is empty")
        return self._responses.pop(0)

    def _consume(self):
        """Attempt to parse buffer into responses.

        This may or may not consume part or the whole of the buffer.
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
        print(" ".join("{:02x}".format(b) for b in bytes_))
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
        self._timeout = timeout if timeout else None
        self._authenticated = False
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

    @property
    def is_authenticated(self):
        """Determine if the connection is authenticated."""
        return self._authenticated

    def _request(self, type_, body):
        request = RCONMessage(0, type_, body)
        self._socket.sendall(request.encode())

    def _receive(self, count=1):
        responses = []
        time_start = time.monotonic()
        while (self._timeout is None
                or time.monotonic() - time_start < self._timeout):
            try:
                i_bytes = self._socket.recv(4096)
            except socket.error:
                raise RCONCommunicationError
            if not i_bytes:
                self.close()
                raise RCONCommunicationError
            self._responses.feed(i_bytes)
            try:
                response = self._responses.pop()
            except RCONError:
                continue
            else:
                responses.append(response)
                if len(responses) == count:
                    return responses
        self.close()
        raise RCONTimeoutError

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
        if self._closed or not self._socket:
            raise RCONError(
                "Cannot authenticate whilst not connected to a server")
        self._request(RCONMessage.Type.AUTH, self._password)
        try:
            # TODO: Understand why two responses -- the first being
            #       completely empty (all zero) -- are sent.
            _, response = self._receive(2)
        except RCONCommunicationError:
            raise RCONAuthenticationError(
                "Server closed connection; you might be banned")
        else:
            if response.id == -1:
                raise RCONAuthenticationError
            self._authenticated = True

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
