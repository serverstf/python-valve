# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import re
import types

import mock
import pytest

from valve.steam.api import interface


class TestEnsureIdentifier(object):

    RE_IDENTIFIER = re.compile(r"[A-Za-z_][0-9A-Za-z_]*")

    def test_strip_bad_chars(self):
        assert interface._ensure_identifier("Upsidé;Down!") == "UpsidDown"

    def test_strip_bad_start(self):
        assert interface._ensure_identifier("123testing123") == "testing123"

    def test_illegal(self):
        with pytest.raises(NameError):
            interface._ensure_identifier("12345!£$%^&*()678909")


def test_make_interfaces(monkeypatch):
    mocks = [mock.Mock(), mock.Mock()]
    mocks_copy = mocks[:]
    mocks[0].__name__ = "TestInterfaceOne"
    mocks[1].__name__ = "TestInterfaceTwo"
    monkeypatch.setattr(interface,
                        "make_interface",
                        mock.Mock(side_effect=lambda *args: mocks.pop(0)))
    interfaces = interface.make_interfaces(
        {
            "apilist": {
                "interfaces": [
                    {"name": "TestInterfaceOne"},
                    {"name": "TestInterfaceTwo"}
                ]
            }
        },
        {"TestInterfaceOne": {"TestMethod": 1}},
    )
    assert isinstance(interfaces, types.ModuleType)
    assert interfaces.__all__ == ["TestInterfaceOne", "TestInterfaceTwo"]
    assert interface.make_interface.call_count == 2
    assert interface.make_interface.call_args_list[0][0][0] == \
        {"name": "TestInterfaceOne"}
    assert interface.make_interface.call_args_list[0][0][1] == {"TestMethod": 1}
    assert interface.make_interface.call_args_list[1][0][0] == \
        {"name": "TestInterfaceTwo"}
    assert interface.make_interface.call_args_list[1][0][1] == {}
    assert interfaces.TestInterfaceOne is mocks_copy[0]
    assert interfaces.TestInterfaceTwo is mocks_copy[1]


class TestMakeInterface(object):

    def test_not_pinned(self, monkeypatch):
        mocks = [mock.Mock(), mock.Mock()]
        mocks_copy = mocks[:]
        mocks[0].name = "TestMethod"
        mocks[0].version = 1
        mocks[1].name = "TestMethod"
        mocks[1].version = 2
        monkeypatch.setattr(interface,
                            "make_method",
                            mock.Mock(side_effect=lambda *args: mocks.pop(0)))
        iface = interface.make_interface(
            {
                "name": "TestInterfaceOne",
                "methods": [
                    {
                        "name": "TestMethod",
                        "version": 1,
                    },
                    {
                        "name": "TestMethod",
                        "version": 2,
                    }
                ],
            },
            {}
        )
        assert issubclass(iface, interface.BaseInterface)
        assert iface.TestMethod.name == "TestMethod"
        assert iface.TestMethod.version == 2
        assert list(iface(mock.Mock())) == [mocks_copy[1]]
        assert interface.make_method.call_count == 2
        assert interface.make_method.call_args_list[0][0][0] == {
            "name": "TestMethod",
            "version": 1,
        }
        assert interface.make_method.call_args_list[1][0][0] == {
            "name": "TestMethod",
            "version": 2,
        }

    def test_pinned(self, monkeypatch):
        mocks = [mock.Mock(), mock.Mock()]
        mocks_copy = mocks[:]
        mocks[0].name = "TestMethod"
        mocks[0].version = 1
        mocks[1].name = "TestMethod"
        mocks[1].version = 2
        monkeypatch.setattr(interface,
                            "make_method",
                            mock.Mock(side_effect=lambda *args: mocks.pop(0)))
        iface = interface.make_interface(
            {
                "name": "TestInterfaceOne",
                "methods": [
                    {
                        "name": "TestMethod",
                        "version": 1,
                    },
                    {
                        "name": "TestMethod",
                        "version": 2,
                    }
                ],
            },
            {
                "TestMethod": 1,
            },
        )
        assert issubclass(iface, interface.BaseInterface)
        assert iface.TestMethod.name == "TestMethod"
        assert iface.TestMethod.version == 1
        assert list(iface(mock.Mock())) == [mocks_copy[0]]
        assert interface.make_method.call_count == 2
        assert interface.make_method.call_args_list[0][0][0] == {
            "name": "TestMethod",
            "version": 1,
        }
        assert interface.make_method.call_args_list[1][0][0] == {
            "name": "TestMethod",
            "version": 2,
        }
