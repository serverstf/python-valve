# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

try:
    import mock
except ImportError:
    import unittest.mock as mock
import pytest

import valve.source
from valve.source import a2s
from valve.source import master_server
from valve.source import messages
from valve.source import util


def test_iter(monkeypatch):
    monkeypatch.setattr(master_server.MasterServerQuerier,
                        "find", mock.Mock(return_value=iter([])))
    msq = master_server.MasterServerQuerier()
    assert iter(msq) is master_server.MasterServerQuerier.find.return_value
    assert master_server.MasterServerQuerier.find.called
    assert master_server.MasterServerQuerier.find.call_args[1] == \
        {"region": "all"}


class TestMapRegion(object):

    @pytest.mark.parametrize("region", [
        master_server.REGION_US_EAST_COAST,
        master_server.REGION_US_WEST_COAST,
        master_server.REGION_SOUTH_AMERICA,
        master_server.REGION_EUROPE,
        master_server.REGION_ASIA,
        master_server.REGION_AUSTRALIA,
        master_server.REGION_MIDDLE_EAST,
        master_server.REGION_AFRICA,
        master_server.REGION_REST,
    ])
    def test_numeric(self, region):
        msq = master_server.MasterServerQuerier()
        assert msq._map_region(region) == [region]

    def test_numeric_invalid(self):
        with pytest.raises(ValueError):
            msq = master_server.MasterServerQuerier()
            msq._map_region(420)

    @pytest.mark.parametrize(("region", "numeric_identifiers"), {
        "na-east": [master_server.REGION_US_EAST_COAST],
        "na-west": [master_server.REGION_US_WEST_COAST],
        "na": [master_server.REGION_US_EAST_COAST,
               master_server.REGION_US_WEST_COAST],
        "sa": [master_server.REGION_SOUTH_AMERICA],
        "eu": [master_server.REGION_EUROPE],
        "as": [master_server.REGION_ASIA, master_server.REGION_MIDDLE_EAST],
        "oc": [master_server.REGION_AUSTRALIA],
        "af": [master_server.REGION_AFRICA],
        "rest": [master_server.REGION_REST],
        "all": [master_server.REGION_US_EAST_COAST,
                master_server.REGION_US_WEST_COAST,
                master_server.REGION_SOUTH_AMERICA,
                master_server.REGION_EUROPE,
                master_server.REGION_ASIA,
                master_server.REGION_AUSTRALIA,
                master_server.REGION_MIDDLE_EAST,
                master_server.REGION_AFRICA,
                master_server.REGION_REST],
    }.items())
    def test_string(self, region, numeric_identifiers):
        msq = master_server.MasterServerQuerier()
        assert set(msq._map_region(region)) == set(numeric_identifiers)

    def test_string_valid(self):
        with pytest.raises(ValueError):
            msq = master_server.MasterServerQuerier()
            msq._map_region("absolutely-ridiculous")

    @pytest.mark.parametrize("region", ["eu", "Eu", "eU", "EU"])
    def test_string_case_sensitivity(self, region):
        msq = master_server.MasterServerQuerier()
        assert msq._map_region(region) == [master_server.REGION_EUROPE]


class TestFind(object):

    @pytest.fixture
    def _map_region(self, monkeypatch):
        monkeypatch.setattr(master_server.MasterServerQuerier,
                            "_map_region", mock.Mock(return_value=["blah"]))
        return master_server.MasterServerQuerier._map_region

    @pytest.fixture
    def _query(self, monkeypatch):
        monkeypatch.setattr(master_server.MasterServerQuerier,
                            "_query", mock.Mock(return_value=[]))
        return master_server.MasterServerQuerier._query

    def test_defaults(self, _map_region, _query, monkeypatch):
        msq = master_server.MasterServerQuerier()
        list(msq.find())
        assert _map_region.called
        assert _map_region.call_args[0][0] == "all"
        assert _query.called
        assert _query.call_args[0][0] == _map_region.return_value[0]
        assert _query.call_args[0][1] == ""

    def test_iterable_region(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(region=["first", "second"]))
        assert _map_region.call_count == 2
        assert _map_region.call_args_list[0][0][0] == "first"
        assert _map_region.call_args_list[1][0][0] == "second"
        assert _query.call_count == \
            len(_map_region.return_value) * _map_region.call_count

    def test_filter_secure(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(secure=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\secure\1"

    def test_filter_linux(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(linux=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\linux\1"

    def test_filter_empty(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(empty=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\empty\1"

    def test_filter_full(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(full=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\full\1"

    def test_filter_proxy(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(proxy=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\proxy\1"

    def test_filter_noplayers(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(noplayers=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\noplayers\1"

    def test_filter_white(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(white=True))
        assert _query.called
        assert _query.call_args[0][1] == r"\white\1"

    # elif key in {"gametype", "gamedata", "gamedataor"}:

    @pytest.mark.parametrize(("filter_term", "filter_", "expected"), [
        ("gametype", ["tag"], r"\gametype\tag"),
        ("gametype", ["tag", "tag2"], r"\gametype\tag,tag2"),
        ("gamedata", ["tag"], r"\gamedata\tag"),
        ("gamedata", ["tag", "tag2"], r"\gamedata\tag,tag2"),
        ("gamedataor", ["tag"], r"\gamedataor\tag"),
        ("gamedataor", ["tag", "tag2"], r"\gamedataor\tag,tag2"),
    ])
    def test_filter_list(self, _map_region, _query,
                         filter_term, filter_, expected):
        msq = master_server.MasterServerQuerier()
        list(msq.find(**{filter_term: filter_}))
        assert _query.called
        assert _query.call_args[0][1] == expected

    @pytest.mark.parametrize("filter_term",
                             ["gametype", "gamedata", "gamedataor"])
    def test_filter_list_empty(self, _map_region, _query, filter_term):
        msq = master_server.MasterServerQuerier()
        list(msq.find(**{filter_term: []}))
        assert _query.called
        assert _query.call_args[0][1] == ""

    @pytest.mark.parametrize("filter_term",
                             ["gametype", "gamedata", "gamedataor"])
    def test_filter_list_all_empty_elements(self, _map_region,
                                            _query, filter_term):
        msq = master_server.MasterServerQuerier()
        list(msq.find(**{filter_term: ["", ""]}))
        assert _query.called
        assert _query.call_args[0][1] == ""

    @pytest.mark.parametrize("filter_term",
                             ["gametype", "gamedata", "gamedataor"])
    def test_filter_list_some_empty_elements(self, _map_region,
                                             _query, filter_term):
        msq = master_server.MasterServerQuerier()
        list(msq.find(**{filter_term: ["tag", "", "tag2"]}))
        assert _query.called
        assert _query.call_args[0][1] == r"\{}\tag,tag2".format(filter_term)

    def test_filter_napp(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(napp=440))
        assert _query.called
        assert _query.call_args[0][1] == r"\napp\440"

    def test_filter_type(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        server_type = util.ServerType(108)
        list(msq.find(type=server_type))
        assert _query.called
        assert _query.call_args[0][1] == r"\type\{}".format(server_type.char)

    def test_filter_type_cast(self, monkeypatch, _map_region, _query):

        class MockServerType(object):

            init_args = []

            def __init__(self, *args, **kwargs):
                self.init_args.append((args, kwargs))

            @property
            def char(self):
                return "d"

        monkeypatch.setattr(util, "ServerType", MockServerType)
        msq = master_server.MasterServerQuerier()
        list(msq.find(type="test"))
        assert util.ServerType.init_args
        assert util.ServerType.init_args[0][0][0] == "test"
        assert _query.called
        assert _query.call_args[0][1] == r"\type\d"

    def test_filter_multiple(self, _map_region, _query):
        msq = master_server.MasterServerQuerier()
        list(msq.find(napp=240, gametype=["tag", "tag2"]))
        assert _query.called
        assert _query.call_args[0][1] == r"\gametype\tag,tag2\napp\240"


class TestQuery(object):

    @pytest.fixture
    def msq(self, monkeypatch):
        monkeypatch.setattr(
            master_server.MasterServerQuerier, "request", mock.Mock())
        monkeypatch.setattr(
            master_server.MasterServerQuerier, "get_response", mock.Mock())
        return master_server.MasterServerQuerier()

    @pytest.fixture
    def request_(self, monkeypatch):
        monkeypatch.setattr(messages, "MasterServerRequest", mock.Mock())
        return messages.MasterServerRequest

    @pytest.fixture
    def response(self, monkeypatch):
        responses = []

        @classmethod
        def mock_decode(cls, raw_response):
            return responses.pop(0)

        monkeypatch.setattr(
            messages.MasterServerResponse,
            "decode",
            mock_decode)

        def add_response(*addresses):
            for batch in addresses:
                fields = {"addresses": [],
                          "start_port": b"26122",
                          "start_host": "255.255.255.255"}
                for address in batch:
                    fields["addresses"].append(
                        messages.MSAddressEntry(host=address[0],
                                                port=address[1]))
                responses.append(messages.MasterServerResponse(**fields))

        return add_response

    def test_initial_request(self, msq, request_, response):
        response([("0.0.0.0", 0)])
        list(msq._query(master_server.REGION_REST, ""))
        assert request_.called
        assert request_.call_args[1] == {
            "region": master_server.REGION_REST,
            "address": "0.0.0.0:0",
            "filter": "",
        }

    def test_single_batch(self, msq, request_, response):
        response([("8.8.8.8", 27015), ("0.0.0.0", 0)])
        addresses = list(msq._query(master_server.REGION_REST, r"\full\1"))
        assert request_.called
        assert request_.call_args[1] == {
            "region": master_server.REGION_REST,
            "address": "0.0.0.0:0",
            "filter": r"\full\1",
        }
        assert addresses == [("8.8.8.8", 27015)]

    def test_multiple_batches(self, msq, request_, response):
        response(
            [
                ("8.8.8.8", 27015),
            ],
            [
                ("8.8.4.4", 27015),
                ("0.0.0.0", 0),
            ],
        )
        addresses = list(msq._query(master_server.REGION_REST, r"\empty\1"))
        assert request_.call_count == 2
        assert request_.call_args_list[0][1] == {
            "region": master_server.REGION_REST,
            "address": "0.0.0.0:0",
            "filter": r"\empty\1",
        }
        assert request_.call_args_list[1][1] == {
            "region": master_server.REGION_REST,
            "address": "8.8.8.8:27015",
            "filter": r"\empty\1",
        }
        assert addresses == [
            ("8.8.8.8", 27015),
            ("8.8.4.4", 27015),
        ]

    def test_no_response(self, msq, request_, response):
        msq.get_response.side_effect = valve.source.NoResponseError
        assert list(msq._query(master_server.REGION_REST, "")) == []
        assert request_.called
        assert request_.call_args[1] == {
            "region": master_server.REGION_REST,
            "address": "0.0.0.0:0",
            "filter": "",
        }

    @pytest.mark.parametrize(("method", "addresses"), [
        (
            master_server.Duplicates.KEEP,
            [
                ("192.0.2.0", 27015),
                ("192.0.2.1", 27015),
                ("192.0.2.2", 27015),
                ("192.0.2.1", 27015),
                ("192.0.2.3", 27015),
            ],
        ),
        (
            master_server.Duplicates.SKIP,
            [
                ('192.0.2.0', 27015),
                ('192.0.2.1', 27015),
                ('192.0.2.2', 27015),
                ('192.0.2.3', 27015),
            ],
        ),
        (
            master_server.Duplicates.STOP,
            [
                ('192.0.2.0', 27015),
                ('192.0.2.1', 27015),
                ('192.0.2.2', 27015),
            ],
        ),
    ])
    def test_duplicates(self, msq, response, method, addresses):
        response([
            ("192.0.2.0", 27015),
            ("192.0.2.1", 27015),
            ("192.0.2.2", 27015),
            ("192.0.2.1", 27015),
            ("192.0.2.3", 27015),
            ("0.0.0.0", 0),
        ])
        # `find` invokes `query` once for every region; so only one region
        assert list(msq.find(region="eu", duplicates=method)) == addresses
