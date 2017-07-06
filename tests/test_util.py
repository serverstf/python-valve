# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import pytest
import six

from valve.source import util


class TestPlatform(object):

    @pytest.mark.parametrize("identifier", [76, 108, 109, 111, 119])
    def test_valid_numeric_identifer(self, identifier):
        platform = util.Platform(identifier)
        assert platform.value == identifier

    def test_invalid_numeric_identifier(self):
        with pytest.raises(ValueError):
            util.Platform(50)

    @pytest.mark.parametrize(("identifier", "expected"), [
        ("L", 76),
        ("l", 108),
        ("m", 109),
        ("o", 111),
        ("w", 119),
    ])
    def test_valid_character_identifier(self, identifier, expected):
        platform = util.Platform(identifier)
        assert platform.value == expected

    def test_invalid_character_identifier(self):
        with pytest.raises(ValueError):
            util.Platform("a")

    @pytest.mark.parametrize(("identifier", "expected"), [
        ("linux", 108),
        ("Linux", 108),
        ("LINUX", 108),
        ("mac os x", 111),  # Note: not 109
        ("Mac OS X", 111),
        ("MAC OS X", 111),
        ("windows", 119),
        ("Windows", 119),
        ("WINDOWS", 119),
    ])
    def test_valid_string_identifier(self, identifier, expected):
        platform = util.Platform(identifier)
        assert platform.value == expected

    def test_invalid_string_identifier(self):
        with pytest.raises(ValueError):
            util.Platform("raindeer")

    def test_empty_string_identifier(self):
        with pytest.raises(ValueError):
            util.Platform("")

    @pytest.mark.parametrize(("identifier", "string"), [
        (76, "Linux"),
        (108, "Linux"),
        (109, "Mac OS X"),
        (111, "Mac OS X"),
        (119, "Windows"),
    ])
    def test_to_unicode(self, identifier, string):
        platform = util.Platform(identifier)
        assert six.text_type(platform) == string

    @pytest.mark.parametrize(("identifier", "string"), [
        (76, b"Linux"),
        (108, b"Linux"),
        (109, b"Mac OS X"),
        (111, b"Mac OS X"),
        (119, b"Windows"),
    ])
    def test_to_bytestring(self, identifier, string):
        platform = util.Platform(identifier)
        assert bytes(platform) == string

    @pytest.mark.parametrize("identifier", [76, 108, 109, 111, 119])
    def test_to_integer(self, identifier):
        platform = util.Platform(identifier)
        assert int(platform) == identifier

    @pytest.mark.parametrize(("identifier", "os_name"), [
        (76, "posix"),
        (108, "posix"),
        (109, "posix"),
        (111, "posix"),
        (119, "nt"),
    ])
    def test_os_name(self, identifier, os_name):
        platform = util.Platform(identifier)
        assert platform.os_name == os_name

    @pytest.mark.parametrize(("platform", "other"), [
        (util.Platform(76), util.Platform(76)),
        (util.Platform(76), util.Platform(108)),  # Starbound
        (util.Platform(108), util.Platform(76)),  # Starbound
        (util.Platform(108), util.Platform(108)),
        (util.Platform(109), util.Platform(109)),
        (util.Platform(111), util.Platform(111)),
        (util.Platform(109), util.Platform(111)),  # Special Mac case
        (util.Platform(111), util.Platform(109)),  # Special Mac case
        (util.Platform(119), util.Platform(119)),
    ])
    def test_equality(self, platform, other):
        assert platform == other

    @pytest.mark.parametrize(("platform", "other"), [
        (util.Platform(76), 76),
        (util.Platform(108), 76),  # Starbound
        (util.Platform(76), 108),  # Starbound
        (util.Platform(108), 108),
        (util.Platform(109), 109),
        (util.Platform(111), 111),
        (util.Platform(109), 111),  # Special Mac case
        (util.Platform(111), 109),  # Special Mac case
        (util.Platform(119), 119),
    ])
    def test_equality_integer(self, platform, other):
        assert platform == other

    @pytest.mark.parametrize(("platform", "other"), [
        (util.Platform(76), "L"),
        (util.Platform(76), "l"),  # Starbound
        (util.Platform(108), "l"),
        (util.Platform(109), "m"),
        (util.Platform(111), "o"),
        (util.Platform(109), "o"),  # Special Mac case
        (util.Platform(111), "m"),  # Special Mac case
        (util.Platform(119), "w"),
    ])
    def test_equality_character(self, platform, other):
        assert platform == other

    @pytest.mark.parametrize(("platform", "other"), [
        (util.Platform(76), "Linux"),
        (util.Platform(108), "Linux"),
        (util.Platform(109), "Mac OS X"),
        (util.Platform(111), "Mac OS X"),
        (util.Platform(119), "Windows"),
    ])
    def test_equality_string(self, platform, other):
        assert platform == other


class TestServerType(object):

    @pytest.mark.parametrize("identifier", [100, 108, 112])
    def test_valid_numeric_identifer(self, identifier):
        server_type = util.ServerType(identifier)
        assert server_type.value == identifier

    def test_invalid_numeric_identifier(self):
        with pytest.raises(ValueError):
            util.ServerType(42)

    @pytest.mark.parametrize(("identifier", "expected"), [
        ("D", 68),
        ("d", 100),
        ("l", 108),
        ("p", 112),
    ])
    def test_valid_character_identifier(self, identifier, expected):
        server_type = util.ServerType(identifier)
        assert server_type.value == expected

    def test_invalid_character_identifier(self):
        with pytest.raises(ValueError):
            util.ServerType("a")

    @pytest.mark.parametrize(("identifier", "expected"), [
        ("dedicated", 100),
        ("Dedicated", 100),
        ("DEDICATED", 100),
        ("non-dedicated", 108),
        ("Non-Dedicated", 108),
        ("NON-DEDICATED", 108),
        ("sourcetv", 112),
        ("SourceTV", 112),
        ("SOURCETV", 112),
    ])
    def test_valid_string_identifier(self, identifier, expected):
        server_type = util.ServerType(identifier)
        assert server_type.value == expected

    def test_invalid_string_identifier(self):
        with pytest.raises(ValueError):
            util.ServerType("snowman")

    def test_empty_string_identifier(self):
        with pytest.raises(ValueError):
            util.Platform("")

    @pytest.mark.parametrize(("identifier", "string"), [
        (68, "Dedicated"),
        (100, "Dedicated"),
        (108, "Non-Dedicated"),
        (112, "SourceTV"),
    ])
    def test_to_unicode(self, identifier, string):
        server_type = util.ServerType(identifier)
        assert six.text_type(server_type) == string

    @pytest.mark.parametrize(("identifier", "string"), [
        (68, b"Dedicated"),
        (100, b"Dedicated"),
        (108, b"Non-Dedicated"),
        (112, b"SourceTV"),
    ])
    def test_to_bytestring(self, identifier, string):
        server_type = util.ServerType(identifier)
        assert bytes(server_type) == string

    @pytest.mark.parametrize("identifier", [68, 100, 108, 112])
    def test_to_integer(self, identifier):
        server_type = util.ServerType(identifier)
        assert int(server_type) == identifier

    @pytest.mark.parametrize(("server_type", "other"), [
        (util.ServerType(68), util.ServerType(68)),
        (util.ServerType(68), util.ServerType(100)),  # Starbound
        (util.ServerType(100), util.ServerType(68)),  # Starbound
        (util.ServerType(100), util.ServerType(100)),
        (util.ServerType(108), util.ServerType(108)),
        (util.ServerType(112), util.ServerType(112)),
    ])
    def test_equality(self, server_type, other):
        assert server_type == other

    @pytest.mark.parametrize(("server_type", "other"), [
        (util.ServerType(68), 68),
        (util.ServerType(100), 68),  # Starbound
        (util.ServerType(68), 100),  # Starbound
        (util.ServerType(100), 100),
        (util.ServerType(108), 108),
        (util.ServerType(112), 112),
    ])
    def test_equality_integer(self, server_type, other):
        assert server_type == other

    @pytest.mark.parametrize(("server_type", "other"), [
        (util.ServerType(68), "D"),
        (util.ServerType(68), "D"),  # Starbound
        (util.ServerType(100), "d"),
        (util.ServerType(108), "l"),
        (util.ServerType(112), "p"),
    ])
    def test_equality_character(self, server_type, other):
        assert server_type == other

    @pytest.mark.parametrize(("server_type", "other"), [
        (util.ServerType(68), "Dedicated"),
        (util.ServerType(100), "Dedicated"),
        (util.ServerType(108), "Non-Dedicated"),
        (util.ServerType(112), "SourceTV"),
    ])
    def test_equality_string(self, server_type, other):
        assert server_type == other
