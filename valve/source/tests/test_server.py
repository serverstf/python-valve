# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)


import pytest


from .. import server


@pytest.srcds_functional(gamedir="tf")
def test_tf2(address):
    try:
        a2s = server.ServerQuerier(address)
        info = a2s.get_info()
    except server.NoResponseError:
        return
    assert info["app_id"] == 440
    assert info["folder"] == "tf"
    assert isinstance(info["folder"], unicode)


@pytest.srcds_functional(gamedir="cstrike")
def test_css(address):
    try:
        a2s = server.ServerQuerier(address)
        info = a2s.get_info()
    except server.NoResponseError:
        return
    assert info["app_id"] == 240
    assert info["folder"] == "cstrike"
    assert isinstance(info["folder"], unicode)


@pytest.srcds_functional(gamedir="csgo")
def test_csgo(address):
    try:
        a2s = server.ServerQuerier(address)
        info = a2s.get_info()
    except server.NoResponseError:
        return
    assert info["app_id"] == 730
    assert info["folder"] == "csgo"
    assert isinstance(info["folder"], unicode)


@pytest.srcds_functional(gamedir="dota")
def test_dota2(address):
    try:
        a2s = server.ServerQuerier(address)
        info = a2s.get_info()
    except server.NoResponseError:
        return
    assert info["app_id"] == 570
    assert info["folder"] == "dota"
    assert isinstance(info["folder"], unicode)


@pytest.srcds_functional(gamedir="left4dead")
def test_l4d(address):
    try:
        a2s = server.ServerQuerier(address)
        info = a2s.get_info()
    except server.NoResponseError:
        return
    assert info["app_id"] == 500
    assert info["folder"] == "left4dead"
    assert isinstance(info["folder"], unicode)


@pytest.srcds_functional(gamedir="left4dead2")
def test_l4d2(address):
    try:
        a2s = server.ServerQuerier(address)
        info = a2s.get_info()
    except server.NoResponseError:
        return
    assert info["app_id"] == 550
    assert info["folder"] == "left4dead2"
    assert isinstance(info["folder"], unicode)
