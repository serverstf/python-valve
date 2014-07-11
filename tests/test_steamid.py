# -*- coding: utf-8 -*-
# Copyright (C) 2014 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import pytest
import six

from valve.steam import id as steamid


class TestSteamID(object):

    def test_account_number_too_small(self):
        with pytest.raises(steamid.SteamIDError):
            steamid.SteamID(-1, 0,
                            steamid.TYPE_INDIVIDUAL,
                            steamid.UNIVERSE_INDIVIDUAL)

    def test_account_number_too_big(self):
        with pytest.raises(steamid.SteamIDError):
            steamid.SteamID(4294967296, 0,
                            steamid.TYPE_INDIVIDUAL,
                            steamid.UNIVERSE_INDIVIDUAL)


@pytest.mark.parametrize(("type_", "as_string"), [
    (steamid.TYPE_ANON_GAME_SERVER, "TYPE_ANON_GAME_SERVER"),
    (steamid.TYPE_INVALID, "TYPE_INVALID"),
    (steamid.TYPE_INDIVIDUAL, "TYPE_INDIVIDUAL"),
    (steamid.TYPE_MULTISEAT, "TYPE_MULTISEAT"),
    (steamid.TYPE_GAME_SERVER, "TYPE_GAME_SERVER"),
    (steamid.TYPE_ANON_GAME_SERVER, "TYPE_ANON_GAME_SERVER"),
    (steamid.TYPE_PENDING, "TYPE_PENDING"),
    (steamid.TYPE_CONTENT_SERVER, "TYPE_CONTENT_SERVER"),
    (steamid.TYPE_CLAN, "TYPE_CLAN"),
    (steamid.TYPE_CHAT, "TYPE_CHAT"),
    (steamid.TYPE_P2P_SUPER_SEEDER, "TYPE_P2P_SUPER_SEEDER"),
    (steamid.TYPE_ANON_USER, "TYPE_ANON_USER"),
])
def test_type_name(type_, as_string):
    id_ = steamid.SteamID(1, 0, type_, steamid.UNIVERSE_INDIVIDUAL)
    assert id_.type_name == as_string


class TestTextRepresentation:

    def test_pending(self):
        id_ = steamid.SteamID(1, 0,
                              steamid.TYPE_PENDING,
                              steamid.UNIVERSE_INDIVIDUAL)
        assert str(id_) == "STEAM_ID_PENDING"

    def test_invalid(self):
        id_ = steamid.SteamID(1, 0,
                              steamid.TYPE_INVALID,
                              steamid.UNIVERSE_INDIVIDUAL)
        assert str(id_) == "UNKNOWN"

    def test_other(self):
        id_ = steamid.SteamID(1, 0,
                              steamid.TYPE_INDIVIDUAL,
                              steamid.UNIVERSE_INDIVIDUAL)
        assert str(id_) == "STEAM_0:0:1"


class Test64CommunityID:

    @pytest.mark.parametrize("type_", [
        steamid.TYPE_INVALID,
        steamid.TYPE_MULTISEAT,
        steamid.TYPE_GAME_SERVER,
        steamid.TYPE_ANON_GAME_SERVER,
        steamid.TYPE_PENDING,
        steamid.TYPE_CONTENT_SERVER,
        steamid.TYPE_CHAT,
        steamid.TYPE_P2P_SUPER_SEEDER,
        steamid.TYPE_ANON_USER,
    ])
    def test_bad_type(self, type_):
        id_ = steamid.SteamID(1, 0, type_, steamid.UNIVERSE_INDIVIDUAL)
        with pytest.raises(steamid.SteamIDError):
            int(id_)

    def test_individual(self):
        id_ = steamid.SteamID(44647673, 0,
                              steamid.TYPE_INDIVIDUAL,
                              steamid.UNIVERSE_INDIVIDUAL)
        assert int(id_) == 76561198049561074

    def test_group(self):
        id_ = steamid.SteamID(44647673, 1,
                              steamid.TYPE_CLAN,
                              steamid.UNIVERSE_INDIVIDUAL)
        assert int(id_) == 103582791518816755
