# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


import types

import mock

from valve.steam.api import interface

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
