# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import pytest
import six

import valve.source
import valve.source.a2s


@pytest.srcds_functional(gamedir="tf")
def test_tf2_ping(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        latency = a2s.ping()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert latency > 0


@pytest.srcds_functional(gamedir="tf")
def test_tf2_info(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        info = a2s.info()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert info["app_id"] == 440
    assert info["folder"] == "tf"
    assert isinstance(info["folder"], six.text_type)


@pytest.srcds_functional(gamedir="tf")
def test_tf2_rules(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        rules = a2s.rules()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")


@pytest.srcds_functional(gamedir="cstrike")
def test_css_ping(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        latency = a2s.ping()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert latency > 0


@pytest.srcds_functional(gamedir="cstrike")
def test_css_info(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        info = a2s.info()
    except valve.source.NoResponseError:
        return
    assert info["app_id"] == 240
    assert info["folder"] == "cstrike"
    assert isinstance(info["folder"], six.text_type)


@pytest.srcds_functional(gamedir="csgo")
def test_csgo_ping(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        latency = a2s.ping()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert latency > 0


@pytest.srcds_functional(gamedir="csgo")
def test_csgo_info(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        info = a2s.info()
    except valve.source.NoResponseError:
        return
    assert info["app_id"] == 730
    assert info["folder"] == "csgo"
    assert isinstance(info["folder"], six.text_type)


@pytest.srcds_functional(gamedir="dota")
def test_dota2_ping(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        latency = a2s.ping()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert latency > 0


@pytest.srcds_functional(gamedir="dota")
def test_dota2_info(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        info = a2s.info()
    except valve.source.NoResponseError:
        return
    assert info["app_id"] == 570
    assert info["folder"] == "dota"
    assert isinstance(info["folder"], six.text_type)


@pytest.srcds_functional(gamedir="left4dead")
def test_l4d_ping(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        latency = a2s.ping()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert latency > 0


@pytest.srcds_functional(gamedir="left4dead")
def test_l4d_info(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        info = a2s.info()
    except valve.source.NoResponseError:
        return
    assert info["app_id"] == 500
    assert info["folder"] == "left4dead"
    assert isinstance(info["folder"], six.text_type)


@pytest.srcds_functional(gamedir="left4dead2")
def test_l4d2_ping(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        latency = a2s.ping()
    except valve.source.NoResponseError:
        pytest.skip("Timedout waiting for response")
    assert latency > 0


@pytest.srcds_functional(gamedir="left4dead2")
def test_l4d2_info(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        info = a2s.info()
    except valve.source.NoResponseError:
        return
    assert info["app_id"] == 550
    assert info["folder"] == "left4dead2"
    assert isinstance(info["folder"], six.text_type)


# quake live
@pytest.srcds_functional(region='rest', appid='282440')
def test_ql_rules(address):
    try:
        a2s = valve.source.a2s.ServerQuerier(address)
        rules = a2s.rules()
    except valve.source.NoResponseError:
        return
