# -*- coding: utf-8 -*-

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import threading

try:
    import mock
except ImportError:
    import unittest.mock as mock
import pytest

import valve.source.a2s
import valve.source.master_server
import valve.testing


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
        except valve.source.NoResponseError:
            pass
        metafunc.parametrize("address", server_addresses)


def pytest_configure():
    pytest.Mock = mock.Mock
    pytest.MagicMock = mock.MagicMock
    pytest.srcds_functional = srcds_functional


@pytest.yield_fixture
def rcon_server():
    server = valve.testing.TestRCONServer()
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    yield server
    server.shutdown()
    thread.join()
