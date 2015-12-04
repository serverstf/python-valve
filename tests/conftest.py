# -*- coding: utf-8 -*-

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import threading
import copy

import pytest
import six.moves.socketserver as socketserver

import valve.source.a2s
import valve.source.master_server
import valve.source.rcon


def srcds_functional(**filter_):
    """Enable SRCDS functional testing for a test case

    This decorator will cause the test case to be parametrised with addresses
    for Source servers as returned from the master server. The test case
    should request a fixture called ``address`` which is a two-item tuple
    of the address of the server.

    All keyword arguments will be converted to a filter string which will
    be used when querying the master server. For example:

    ```
    @srcds_functional(gamedir="tf")
    def test_foo(address):
        pass
    ```

    This will result in the test only being ran on TF2 servers. See the link
    below for other filter options:

    https://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol#Filter
    """

    def decorator(function):
        function._srcds_filter = filter_
        return function

    return decorator


def pytest_addoption(parser):
    parser.addoption("--srcds-functional",
                     action="store_true",
                     default=False,
                     dest="srcds_functional",
                     help="Enable A2S functional tests against 'real' servers")
    parser.addoption("--srcds-functional-limit",
                     action="store",
                     type=int,
                     default=20,
                     help=("Limit the number of servers srcds_functional "
                           "tests are ran against. Set to 0 to run against "
                           "*all* servers -- warning: really slow"),
                     dest="srcds_functional_limit")


def pytest_generate_tests(metafunc):
    """Generate parametrised tests from real Source server instances

    This will apply an 'address' parametrised fixture for all rests marked
    with srcds_functional which is a two-item tuple address for a public
    Source server.

    This uses the MasterServerQuerier to find public server addressess from
    all regions. Filters passed into ``@srcds_functional`` will be used when
    querying the master server.
    """
    if hasattr(metafunc.function, "_srcds_filter"):
        if not metafunc.config.getoption("srcds_functional"):
            pytest.skip("--srcds-functional not enabled")
        if "address" not in metafunc.fixturenames:
            raise Exception("You cannot use the srcds_functional decorator "
                            "without requesting an 'address' fixture")
        msq = valve.source.master_server.MasterServerQuerier()
        server_addresses = []
        address_limit = metafunc.config.getoption("srcds_functional_limit")
        region = metafunc.function._srcds_filter.pop('region', 'eu')
        try:
            for address in msq.find(region=region,
                                    **metafunc.function._srcds_filter):
                if address_limit:
                    if len(server_addresses) >= address_limit:
                        break
                server_addresses.append(address)
        except valve.source.a2s.NoResponseError:
            pass
        metafunc.parametrize("address", server_addresses)


def pytest_namespace():
    return {"srcds_functional": srcds_functional}


class ExpectedRCONMessage(valve.source.rcon.RCONMessage):

    def __init__(self, id_, type_, body):
        valve.source.rcon.RCONMessage.__init__(self, id_, type_, body)
        self._responses = []

    def respond(self, id_, type_, body):
        self._responses.append(
            valve.source.rcon.RCONMessage(id_, type_, body))

    def encode_responses(self):
        return b"".join(response.encode() for response in self._responses)


class TestRCONHandler(socketserver.BaseRequestHandler):

    def _decode_messages(self, buffer_):
        while buffer_:
            try:
                message, buffer_ = \
                    valve.source.rcon.RCONMessage.decode(buffer_)
            except valve.source.rcon.RCONMessageError:
                return
            else:
                yield message

    def _handle_request(self, message):
        if not self._expectations:
            raise Exception("Unexpected message {}".format(message))
        expected = self._expectations.pop(0)
        for attribute in ['id', 'type', 'body']:
            a_message = getattr(message, attribute)
            a_expected = getattr(expected, attribute)
            if a_message != a_expected:
                raise Exception("Expected {} == {!r}, got {!r}".format(
                    attribute, a_expected, a_message))
        self.request.sendall(expected.encode_responses())

    def setup(self):
        self._expectations = self.server.expectations()

    def handle(self):
        buffer_ = b""
        while True:
            received = self.request.recv(4096)
            if not received:
                return
            buffer_ += received
            for message in self._decode_messages(buffer_):
                self._handle_request(message)


class TestRCONServer(socketserver.TCPServer):

    def __init__(self):
        socketserver.TCPServer.__init__(self, ('', 0), TestRCONHandler)
        self._expectations = []

    def expect(self, id_, type_, body):
        self._expectations.append(ExpectedRCONMessage(id_, type_, body))
        return self._expectations[-1]

    def expectations(self):
        return copy.deepcopy(self._expectations)


@pytest.yield_fixture
def rcon_server():
    server = TestRCONServer()
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    yield server
    server.shutdown()
    thread.join()
