# -*- coding: utf-8 -*-
# Copyright (C) 2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import socket

import pytest

import valve.source


class TestBaseQuerier:

    def test(self):
        querier = valve.source.BaseQuerier(('192.0.2.0', 27015))
        assert querier.host == '192.0.2.0'
        assert querier.port == 27015
        assert querier._socket.family == socket.AF_INET
        assert querier._socket.type == socket.SOCK_DGRAM
        querier.close()
        assert querier._socket is None

    def test_close(self):
        querier = valve.source.BaseQuerier(('192.0.2.0', 27015))
        assert querier._socket.family == socket.AF_INET
        assert querier._socket.type == socket.SOCK_DGRAM
        querier.close()
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()

    def test_close_redundant(self):
        querier = valve.source.BaseQuerier(('192.0.2.0', 27015))
        assert querier._socket.family == socket.AF_INET
        assert querier._socket.type == socket.SOCK_DGRAM
        querier.close()
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()
        querier.close()
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()

    def test_context_manager(self):
        with valve.source.BaseQuerier(('192.0.2.0', 27015)) as querier:
            assert querier._socket.family == socket.AF_INET
            assert querier._socket.type == socket.SOCK_DGRAM
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()

    def test_context_manager_close_before_exit(self):
        with valve.source.BaseQuerier(('192.0.2.0', 27015)) as querier:
            assert querier._socket.family == socket.AF_INET
            assert querier._socket.type == socket.SOCK_DGRAM
            with pytest.warns(UserWarning):
                querier.close()
            assert querier._socket is None
            with pytest.raises(valve.source.QuerierClosedError):
                querier.request()
            with pytest.raises(valve.source.QuerierClosedError):
                querier.get_response()
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()

    def test_context_manager_close_after_exit(self):
        with valve.source.BaseQuerier(('192.0.2.0', 27015)) as querier:
            assert querier._socket.family == socket.AF_INET
            assert querier._socket.type == socket.SOCK_DGRAM
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()
        querier.close()
        assert querier._socket is None
        with pytest.raises(valve.source.QuerierClosedError):
            querier.request()
        with pytest.raises(valve.source.QuerierClosedError):
            querier.get_response()
