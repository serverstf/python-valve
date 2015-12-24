"""Utilities for testing."""

import copy
import functools
import select

import six.moves.socketserver as socketserver

import valve.rcon


class UnexpectedRCONMessage(Exception):
    """Raised when an RCON request wasn't expected."""


class ExpectedRCONMessage(valve.rcon.RCONMessage):
    """Request expected by :class:`TestRCONServer`.

    This class should not be instantiated directly. Instead use the
    :meth:`TestRCONServer.expect` factory to create them.

    Instances of this class can be configured to respond to the request
    using :meth:`respond`, :meth:`response_close`, etc..
    """

    def __init__(self, id_, type_, body):
        valve.rcon.RCONMessage.__init__(self, id_, type_, body)
        self.responses = []

    def respond(self, id_, type_, body):
        """Respond to the request with a message.

        The parameters for this method are the same as those given to
        the initialise of :class:`valve.rcon.RCONMessage`. The created
        message will be encoded and sent to the client.
        """
        response = functools.partial(
            _TestRCONHandler.send_message,
            message=valve.rcon.RCONMessage(id_, type_, body),
        )
        self.responses.append(response)

    def respond_close(self):
        """Respond by closing the connection."""
        self.responses.append(_TestRCONHandler.close)

    def respond_terminate_multi_part(self, id_):
        """Respond by sending a multi-part message terminator.

        :class:`valve.rcon.RCON` always expects multi-part responses so you
        must configure one of these responses whenver you :meth:`respond`
        with a :class:`valve.rcon.RCONMessage.Type.RESPONSE_VALVE`-type
        message.
        """
        self.respond(
            id_, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        self.respond(
            id_,
            valve.rcon.RCONMessage.Type.RESPONSE_VALUE,
            b"\x00\x01\x00\x00",
        )


class _TestRCONHandler(socketserver.BaseRequestHandler):
    """Request handler for :class:`TestRCONServer`."""

    def _decode_messages(self):
        """Decode buffer into discrete RCON messages.

        This may consume the buffer, either in whole or part.

        :returns: an iterator of :class:`valve.rcon.RCONMessage`s.
        """
        while self._buffer:
            try:
                message, self._buffer = \
                    valve.rcon.RCONMessage.decode(self._buffer)
            except valve.rcon.RCONMessageError:
                return
            else:
                yield message

    def _handle_request(self, message):
        """Handle individual RCON requests.

        Given a RCON request this will check that it matches the next
        expected request by comparing the request's ID, type and body
        attributes. If they all match, then each of the responses
        configured for the request is called.

        :param valve.rcon.RCONMessage: the request to handle.

        :raises UnexpectedRCONMessage: if given message does not match
            the expected request.
        """
        if not self._expectations:
            raise UnexpectedRCONMessage(
                "Unexpected message {}".format(message))
        expected = self._expectations.pop(0)
        for attribute in ['id', 'type', 'body']:
            a_message = getattr(message, attribute)
            a_expected = getattr(expected, attribute)
            if a_message != a_expected:
                raise UnexpectedRCONMessage(
                    "Expected {} == {!r}, got {!r}".format(
                    attribute, a_expected, a_message))
        for response in expected.responses:
            response(self)

    def send_message(self, message):
        self.request.sendall(message.encode())

    def close(self):
        self.request.close()

    def setup(self):
        self._buffer = b""
        self._expectations = self.server.expectations()

    def handle(self):
        """Handle incoming requests.

        This will continually read incoming requests from the connected
        socket assigned to this handler. If the connected client closes
        the connection this method will exit.
        """
        while True:
            ready, _, _ = select.select([self.request], [], [], 0)
            if ready:
                received = self.request.recv(4096)
                if not received:
                    return
                self._buffer += received
                try:
                    for message in self._decode_messages():
                        self._handle_request(message)
                except UnexpectedRCONMessage:
                    return


class TestRCONServer(socketserver.TCPServer):
    """Stub RCON server for testing.

    This class provides a simple RCON server which can be configured to
    respond to requests in certain ways. The idea is that this can be used
    in testing to fake the responses from a real RCON server.

    Specifically, each instance of this server can be configured to
    :meth:`expect` requests in a certain order. For each expected request
    there can be any number of responses for it. Each connection to the
    server will expect the exact same requests.

    All expected requests should be configured *before* connecting the
    client to the server.

    :param address: the address the server should bind to. By default it
        will use a random port on all interfaces. In such cases the actual
        address in use can be retrieved via the :attr:`server_address`
        attribute.
    """

    def __init__(self, address=('', 0)):
        socketserver.TCPServer.__init__(self, ('', 0), _TestRCONHandler)
        self._expectations = []

    def expect(self, id_, type_, body):
        """Expect a RCON request.

        The parameters for this method are the same as those passed to the
        initialiser of :class:`ExpectedRCONMessage`.

        :returns: the corresponding :class:`ExpectedRCONMessage`.
        """
        self._expectations.append(ExpectedRCONMessage(id_, type_, body))
        return self._expectations[-1]

    def expectations(self):
        """Get a copy of all the expectations.

        :returns: a deep copy of all the :class:`ExpectedRCONMessage`
            configured for the server.
        """
        return copy.deepcopy(self._expectations)
