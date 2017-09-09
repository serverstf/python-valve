# -*- coding: utf-8 -*-
# Copyright (C) 2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import select
import socket


class NoResponseError(Exception):
    """Raised when a server querier doesn't receive a response."""


class BaseServerQuerier(object):
    """Base class for implementing source server queriers.

    :ivar host: Host requests will be sent to.
    :ivar port: Port number requests will be sent to.
    :ivar timeout: How long to wait for a response to a request.
    """

    def __init__(self, address, timeout=5.0):
        self.host = address[0]
        self.port = address[1]
        self.timeout = timeout
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def request(self, *request):
        """Issue a request.

        The given request segments will be encoded and combined to
        form the final message that is sent to the configured address.

        :param request: Request message segments.
        :param request: valve.source.messages.Message
        """
        request_final = b"".join(segment.encode() for segment in request)
        self._socket.sendto(request_final, (self.host, self.port))

    def get_response(self):
        """Wait for a response to a request.

        :raises NoResponseError: If the configured :attr:`timeout` is
            reached before a response is received.

        :returns: The raw response as a :class:`bytes`.
        """
        ready = select.select([self._socket], [], [], self.timeout)
        if not ready[0]:
            raise NoResponseError("Timed out waiting for response")
        try:
            data = ready[0][0].recv(1400)
        except socket.error as exc:
            raise NoResponseError(exc) from exc
        return data
