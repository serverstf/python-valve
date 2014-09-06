# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import re
import textwrap
import types

import mock
import pytest

from valve.steam.api import interface


class TestEnsureIdentifier(object):

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


class TestMethodParameters(object):

    def test_ignore_key(self):
        params = interface._MethodParameters([
            {
                "name": "key",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
        ])
        assert "key" not in params

    def test_duplicate_name(self):
        with pytest.raises(NameError):
            params = interface._MethodParameters([
                {
                    "name": "test",
                    "type": "string",
                    "optional": False,
                    "description": "test parameter",
                },
                {
                    "name": "test",
                    "type": "string",
                    "optional": False,
                    "description": "test parameter",
                }
            ])

    def test_missing_description(self):
        params = interface._MethodParameters([
            {
                "name": "test",
                "type": "string",
                "optional": False,
            },
        ])
        param = params["test"]
        assert param["name"] == "test"
        assert param["type"] == "string"
        assert param["optional"] is False
        assert param["description"] == ""

    def test_unknown_type(self):
        params = interface._MethodParameters([
            {
                "name": "test",
                "type": "",
                "optional": False,
                "description": "test parameter",
            },
        ])
        param = params["test"]
        assert param["name"] == "test"
        assert param["type"] == "string"
        assert param["optional"] is False
        assert param["description"] == "test parameter"

    def test_sorted(self):
        params = interface._MethodParameters([
            {
                "name": "zebra",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
            {
                "name": "aardvark",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
        ])
        assert list(params.keys()) == ["aardvark", "zebra"]

    def test_signature(self):
        params = interface._MethodParameters([
            {
                "name": "zebra",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
            {
                "name": "aardvark",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
            {
                "name": "xenopus",
                "type": "string",
                "optional": True,
                "description": "test parameter",
            },
            {
                "name": "bullfrog",
                "type": "string",
                "optional": True,
                "description": "test parameter",
            },
        ])
        assert params.signature == \
            "self, aardvark, zebra, bullfrog=None, xenopus=None"

    def test_signature_no_params(self):
        params = interface._MethodParameters([])
        assert params.signature == "self"

    def test_validate_missing_mandatory(self):
        params = interface._MethodParameters([
            {
                "name": "test",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
        ])
        with pytest.raises(TypeError):
            params.validate()

    def test_validate_skip_missing_optional(self):
        params = interface._MethodParameters([
            {
                "name": "test",
                "type": "string",
                "optional": True,
                "description": "test parameter",
            },
        ])
        assert params.validate(test=None) == {}

    def test_validate_type_conversion(self, monkeypatch):
        validator = mock.Mock()
        monkeypatch.setattr(interface,
                            "PARAMETER_TYPES", {"string": validator})
        params = interface._MethodParameters([
            {
                "name": "test",
                "type": "string",
                "optional": False,
                "description": "test parameter",
            },
        ])
        assert params.validate(test="raw value") == {
            "test": validator.return_value}
        assert validator.called
        assert validator.call_args[0][0] == "raw value"


def test_make_method():
    method = interface.make_method({
        "name": "test",
        "version": 1,
        "httpmethod": "GET",
        "parameters": [
            {
                "name": "foo",
                "type": "string",
                "optional": False,
                "description": "foo docs",
            },
            {
                "name": "bar",
                "type": "string",
                "optional": True,
                "description": "bar docs",
            },
        ],
    })
    assert method.__name__ == "test"
    assert method.name == "test"
    assert method.version == 1
    assert method.__doc__ == textwrap.dedent("""\
        :param string bar: bar docs
        :param string foo: foo docs""")
    assert method.__defaults__ == (None,)
    iface = mock.Mock()
    method(iface, "foo")
    assert iface._request.called
    assert iface._request.call_args[0][0] == "GET"
    assert iface._request.call_args[0][1] == "test"
    assert iface._request.call_args[0][2] == 1
    assert iface._request.call_args[0][3] == {"foo": "foo"}
