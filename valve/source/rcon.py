# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Oliver Ainsworth

"""
    Provides an interface to the Source Dedicated Server (SRCDS) remote
    console (RCON), allow you to issue commands to a server remotely.
"""

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import errno
import os
import socket
import struct
import time


WOULDBLOCK = [errno.EAGAIN, errno.EWOULDBLOCK]
if os.name == "nt":
    WOULDBLOCK.append(errno.WSAEWOULDBLOCK)


class IncompleteMessageError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class NoResponseError(Exception):
    pass


class Message(object):

    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0

    def __init__(self, id, type, body=""):
        self.id = id
        self.type = type
        self.body = body
        self.response = None

    def __str__(self):
        types = {
            Message.SERVERDATA_AUTH: "SERVERDATA_AUTH",
            Message.SERVERDATA_AUTH_RESPONSE: ("SERVERDATA_AUTH_RESPONSE/"
                                               "SERVERDATA_EXECCOMAND"),
            Message.SERVERDATA_RESPONSE_VALUE: "SERVERDATA_RESPONSE_VALUE"
        }
        return "{type} ({id}) '{body}'".format(
            type=types.get(self.type, "INVALID"),
            id=self.id,
            body=" ".join([c.encode("hex") for c in self.body])
        )

    @property
    def size(self):
        """
            Packet size in bytes, minus the 'size' fields (4 bytes).
        """
        return struct.calcsize(b"<ii") + len(self.body.encode("ascii")) + 2

    def encode(self):
        """Encode the message to a bytestring

        Each packed message inludes the payload size (in bytes,) message ID
        and message type encoded into a 12 byte header. The header is followed
        by a null-terimnated ASCII-encoded string and a further trailing null
        terminator.
        """
        return (struct.pack(b"<iii", self.size, self.id, self.type) +
                self.body.encode("ascii") + b"\x00\x00")

    @classmethod
    def decode(cls, buffer):
        """
            Will attempt to decode a single message from a byte buffer,
            returning a corresponding Message instance and the remaining
            buffer contents if any.

            If buffer is does not contain at least one full message,
            IncompleteMessageError is raised.
        """

        if len(buffer) < struct.calcsize(b"<i"):
            raise IncompleteMessageError
        size = struct.unpack(b"<i", buffer[:4])[0]
        if len(buffer) - struct.calcsize(b"<i") < size:
            raise IncompleteMessageError
        packet = buffer[:size + 4]
        buffer = buffer[size + 4:]
        id = struct.unpack(b"<i", packet[4:8])[0]
        type = struct.unpack(b"<i", packet[8:12])[0]
        body = packet[12:][:-2].decode("ascii", "ignore")
        return cls(id, type, body), buffer


class RCON(object):

    def __init__(self, address, password=None, timeout=10.0):
        self.host = address[0]
        self.port = address[1]
        self.password = password
        self.timeout = timeout
        self._next_id = 1
        self._read_buffer = b""
        self._active_requests = {}
        self._response = []
        self._socket = None
        self.is_authenticated = False

    def __enter__(self):
        """Connect and optionally authenticate to the server

        Authentication will only be attempted if the :attr:`.password`
        attribute is set.
        """
        self.connect()
        if self.password:
            self.authenticate(self.password)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Disconnect from the server"""
        self.disconnect()
        self.is_authenticated = False
        self._next_id = 0

    def __call__(self, command):
        """Execute a command on the server

        This wraps :meth:`.execute` but returns the response body instead of
        the request :class:`Message` object.
        """
        return self.execute(command).response.body

    def connect(self):
        """Connect to host, creating transport if necessary"""
        if not self._socket:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.host, self.port))
        self._socket.settimeout(0.0)

    def disconnect(self):
        self._socket.close()
        self.is_authenticated = False

    def request(self, type, body=u""):
        """
            Send a message to server.

            If type is SEVERDATA_EXECCOMAND
            an addtional SERVERDATA_RESPONSE_VALUE is sent in order
            to facilitate correct processing of multi-packet responses.
        """

        request = Message(self._next_id, type, body)
        self._active_requests[request.id] = request
        self._next_id += 1
        self._socket.sendall(request.encode())
        # Must send a SERVERDATA_RESPONSE_VALUE after EXECCOMMAND
        # in order to handle multi-packet responses as per
        # https://developer.valvesoftware.com/wiki/RCON#Multiple-packet_Responses
        if type == Message.SERVERDATA_EXECCOMAND:
            self.request(Message.SERVERDATA_RESPONSE_VALUE)
        return request

    def process(self):
        """
            Reads all avilable data from socket and attempts to process
            a response. Responses are automatically attached to their
            corresponding request.
        """

        try:
            self._read_buffer += self._socket.recv(4096)
        except socket.error as exc:
            if exc.errno not in WOULDBLOCK:
                raise
        response, self._read_buffer = Message.decode(self._read_buffer)
        # Check if terminating RESPONSE_VALUE with body 00 01 00 00
        if (response.type == Message.SERVERDATA_RESPONSE_VALUE and
                response.body.encode("ascii") == b"\x00\x01\x00\x00"):
            response = Message(self._response[0].id,
                               self._response[0].type,
                               "".join([r.body for r in self._response]))
            self._active_requests[response.id].response = response
            self._response = []
            self._active_requests[response.id]
        elif response.type == Message.SERVERDATA_RESPONSE_VALUE:
            self._response.append(response)
        elif response.type == Message.SERVERDATA_AUTH_RESPONSE:
            self._active_requests[self._response[0].id].response = response
            # Clear empty SERVERDATA_RESPONSE_VALUE sent before
            # SERVERDATA_AUTH_RESPONSE
            self._response = []
            self._active_requests[response.id]

    def response_to(self, request, timeout=None):
        """
            Returns a context manager that waits up to a given time for
            a response to a specific request. Assumes the request has
            actually been sent to an RCON server.

            If the timeout period is exceeded, NoResponseError is raised.
        """

        class ResponseContextManager(object):

            def __init__(self, rcon, request, timeout):
                self.rcon = rcon
                self.request = request
                self.timeout = timeout

            def __enter__(self):
                time_left = self.timeout
                while self.request.response is None:
                    time_start = time.time()
                    try:
                        self.rcon.process()
                    except IncompleteMessageError:
                        pass
                    time_left -= time.time() - time_start
                    if time_left < 0:
                        raise NoResponseError
                return self.request.response

            def __exit__(self, type, value, tb):
                pass

        if timeout is None:
            timeout = self.timeout
        return ResponseContextManager(self, request, timeout)

    def authenticate(self, password):
        """
            Authenticates with the server using the given password.

            Raises AuthenticationError if password is incorrect. Note
            that multiple attempts with the wrong password will result
            in the server automatically banning 'this' IP.
        """
        request = self.request(Message.SERVERDATA_AUTH, unicode(password))
        with self.response_to(request) as response:
            if response.id == -1:
                raise AuthenticationError
            self.is_authenticated = True

    def execute(self, command, block=True):
        """
            Executes a SRCDS console command.

            Returns the Message object that makes up the request sent
            to the server. If block is True, the response attribute
            will be set, unless a NoResposneError was raised whilst
            waiting for a response.

            If block is False, calls must be made to process() until
            a response is recieved. E.g. use response_to().

            Requires that the client is authenticated, otherwise an
            AuthenticationError is raised.
        """

        if not self.is_authenticated:
            raise AuthenticationError
        request = self.request(Message.SERVERDATA_EXECCOMAND, unicode(command))
        if block:
            with self.response_to(request):
                pass
        return request


def shell(rcon=None):

    def prompt(prompt=None):
        if prompt:
            return raw_input("{}: ".format(prompt))
        else:
            return raw_input("{}:{}>".format(rcon.host, rcon.port))

    if rcon is None:
        rcon = RCON((prompt("host"), int(prompt("port"))))
    if not rcon.is_authenticated:
        rcon.authenticate(prompt("password"))
    while True:
        cmd = rcon.execute(prompt())
        with rcon.response_to(cmd) as response:
            print(response.body)
