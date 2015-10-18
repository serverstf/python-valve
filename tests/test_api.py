# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import re
import textwrap
import types

try:
    import mock
except ImportError:
    import unittest.mock as mock
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


class TestAPI(object):

    @pytest.fixture
    def interfaces(self):
        module = types.ModuleType(str("test"))
        module.TestInterface = type(
            str("TestInterface"), (interface.BaseInterface,), {})
        return module

    @pytest.mark.parametrize(("format_name", "format_func"), [
        ("json", interface.json_format),
        ("xml", interface.etree_format),
        ("vdf", interface.vdf_format),
    ])
    def test_formats(self, monkeypatch, format_name, format_func):
        monkeypatch.setattr(interface, "make_interfaces", mock.Mock())
        monkeypatch.setattr(interface.API, "_bind_interfaces", mock.Mock())
        monkeypatch.setattr(interface.API, "request", mock.Mock())
        api = interface.API(format=format_name)
        assert api.format is format_func
        assert interface.make_interfaces.called
        assert (interface.make_interfaces.call_args[0][0]
                is api.request.return_value)
        assert interface.make_interfaces.call_args[0][1] == {}
        assert api.request.called
        assert api.request.call_args[0][0] == "GET"
        assert api.request.call_args[0][1] == "ISteamWebAPIUtil"
        assert api.request.call_args[0][2] == "GetSupportedAPIList"
        assert api.request.call_args[0][3] == 1
        assert api.request.call_args[1]["format"] is interface.json_format
        assert api._bind_interfaces.called

    def test_inherit_interfaces(self, monkeypatch):
        monkeypatch.setattr(interface, "make_interfaces", mock.Mock())
        monkeypatch.setattr(interface.API, "_bind_interfaces", mock.Mock())
        monkeypatch.setattr(interface.API, "request", mock.Mock())
        interfaces = types.ModuleType(str("test"))
        api = interface.API(interfaces=interfaces)
        assert api._interfaces_module == interfaces
        assert not interface.make_interfaces.called
        assert api._bind_interfaces.called
        assert not api.request.called

    def test_getitem(self):
        api = interface.API(interfaces=types.ModuleType(str("test")))
        api._interfaces = mock.MagicMock()
        assert api["Test"] is api._interfaces.__getitem__.return_value
        assert api._interfaces.__getitem__.call_args[0][0] == "Test"

    def test_bind_interfaces(self, interfaces):
        interfaces.NotSubClass = type(str("NotSubClass"), (), {})
        interface.not_a_class = None
        api = interface.API(interfaces=interfaces)
        assert isinstance(api["TestInterface"], interface.BaseInterface)
        with pytest.raises(KeyError):
            api["NotSubClass"]

    def test_request(self, interfaces):
        api = interface.API(interfaces=interfaces)
        api._session = mock.Mock()
        api.format = mock.Mock(format="json")
        request = api._session.request
        raw_response = request.return_value
        response = api.request("GET", "interface", "method",
                               1, params={"key": "test", "foo": "bar"})
        assert api.format.called
        assert api.format.call_args[0][0] is raw_response.text
        assert request.call_args[0][0] == "GET"
        assert request.call_args[0][1] == api.api_root + "interface/method/v1/"
        assert request.call_args[0][2] == {"format": "json", "foo": "bar"}

    @pytest.mark.parametrize("format_", ["json", "xml", "vdf"])
    def test_request_with_key(self, interfaces, format_):
        api = interface.API(key="key", interfaces=interfaces)
        api._session = mock.Mock()
        api.format = mock.Mock(format=format_)
        request = api._session.request
        raw_response = request.return_value
        response = api.request("GET", "interface", "method",
                               1, params={"key": "test", "foo": "bar"})
        assert api.format.called
        assert api.format.call_args[0][0] is raw_response.text
        assert request.call_args[0][0] == "GET"
        assert request.call_args[0][1] == api.api_root + "interface/method/v1/"
        assert request.call_args[0][2] == {
            "key": "key",
            "format": format_,
            "foo": "bar",
        }

    def test_request_unknown_format(self, interfaces):
        api = interface.API(interfaces=interfaces)
        api._session = mock.Mock()
        api.format = mock.Mock(format="invalid")
        request = api._session.request
        raw_response = request.return_value
        with pytest.raises(ValueError):
            api.request("GET", "interface", "method", 1)

    def test_iter(self, interfaces):
        api = interface.API(interfaces=interfaces)
        foo = object()
        bar = object()
        api._interfaces = {"foo": foo, "bar": bar}
        list_ = list(api)
        assert len(list_) == 2
        assert foo in list_
        assert bar in list_

    def test_versions(self, interfaces):
        api = interface.API(interfaces=interfaces)
        ifoo = mock.MagicMock()
        ifoo.name = "ifoo"
        ifoo_meths = [mock.Mock(version=1), mock.Mock(version=2)]
        ifoo_meths[0].name = "eggs"
        ifoo_meths[1].name = "spam"
        ifoo.__iter__ = lambda i: iter(ifoo_meths)
        ibar = mock.MagicMock()
        ibar.name = "ibar"
        ibar_meths = [mock.Mock(version=1)]
        ibar_meths[0].name = "method"
        ibar.__iter__ = lambda i: iter(ibar_meths)
        api._interfaces = {
            "ifoo": ifoo,
            "ibar": ibar,
        }
        assert api.versions() == {
            "ifoo": {"eggs": 1, "spam": 2},
            "ibar": {"method": 1},
        }
