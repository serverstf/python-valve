# -*- coding: utf-8 -*-
# Copyright (C) 2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import select
import socket


class NoResponseError(Exception):
    """Raised when a server querier doesn't receive a response."""


class BaseServerQuerier(object):

    def __init__(self, address, timeout=5.0):
        self.host = address[0]
        self.port = address[1]
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def request(self, request):
        self.socket.sendto(request.encode(), (self.host, self.port))

    def get_response(self):
        ready = select.select([self.socket], [], [], self.timeout)
        if not ready[0]:
            raise NoResponseError("Timed out waiting for response")
        try:
            data = ready[0][0].recv(1400)
        except socket.error as exc:
            raise NoResponseError(exc)
        return data
