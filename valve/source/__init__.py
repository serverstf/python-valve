# -*- coding: utf-8 -*-
# Copyright (C) 2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import functools
import select
import socket
import warnings

import six


class NoResponseError(Exception):
    """Raised when a server querier doesn't receive a response."""


class QuerierClosedError(Exception):
    """Raised when attempting to use a querier after it's closed."""


class BaseQuerier(object):
    """Base class for implementing source server queriers.

    When an instance of this class is initialised a socket is created.
    It's important that, once a querier is to be discarded, the associated
    socket be closed via :meth:`close`. For example:

    .. code-block:: python

        querier = valve.source.BaseQuerier(('...', 27015))
        try:
            querier.request(...)
        finally:
            querier.close()

    When server queriers are used as context managers, the socket will
    be cleaned up automatically. Hence it's preferably to use the `with`
    statement over the `try`-`finally` pattern described above:

    .. code-block:: python

        with valve.source.BaseQuerier(('...', 27015)) as querier:
            querier.request(...)

    Once a querier has been closed, any attempts to make additional requests
    will result in a :exc:`QuerierClosedError` to be raised.

    :ivar host: Host requests will be sent to.
    :ivar port: Port number requests will be sent to.
    :ivar timeout: How long to wait for a response to a request.
    """

    def __init__(self, address, timeout=5.0):
        self.host = address[0]
        self.port = address[1]
        self.timeout = timeout
        self._contextual = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __enter__(self):
        self._contextual = True
        return self

    def __exit__(self, type_, exception, traceback):
        self._contextual = False
        self.close()

    def _check_open(function):
        # Wrap methods to raise QuerierClosedError when called
        # after the querier has been closed.

        @functools.wraps(function)
        def wrapper(self, *args, **kwargs):
            if self._socket is None:
                raise QuerierClosedError
            return function(self, *args, **kwargs)

        return wrapper

    def close(self):
        """Close the querier's socket.

        It is safe to call this multiple times.
        """
        if self._contextual:
            warnings.warn("{0.__class__.__name__} used as context "
                          "manager but close called before exit".format(self))
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    @_check_open
    def request(self, *request):
        """Issue a request.

        The given request segments will be encoded and combined to
        form the final message that is sent to the configured address.

        :param request: Request message segments.
        :type request: valve.source.messages.Message

        :raises QuerierClosedError: If the querier has been closed.
        """
        request_final = b"".join(segment.encode() for segment in request)
        self._socket.sendto(request_final, (self.host, self.port))

    @_check_open
    def get_response(self):
        """Wait for a response to a request.

        :raises NoResponseError: If the configured :attr:`timeout` is
            reached before a response is received.
        :raises QuerierClosedError: If the querier has been closed.

        :returns: The raw response as a :class:`bytes`.
        """
        ready = select.select([self._socket], [], [], self.timeout)
        if not ready[0]:
            raise NoResponseError("Timed out waiting for response")
        try:
            data = ready[0][0].recv(65536)
        except socket.error as exc:
            six.raise_from(NoResponseError(exc))
        return data

    del _check_open
