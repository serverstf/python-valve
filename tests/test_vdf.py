# -*- coding: utf-8 -*-
# Copyright (C) 2017 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import pytest

import valve.vdf


@pytest.fixture
def transcluder():
    return valve.vdf.VDFTestTranscluder()


class TestVDFIgnoreTranscluder:

    def test(self):
        transcluder = valve.vdf.VDFIgnoreTranscluder()
        assert "".join(transcluder.transclude("foo")) == ""


class TestVDFDisabledTranscluder:

    def test(self):
        transcluder = valve.vdf.VDFDisabledTranscluder()
        with pytest.raises(valve.vdf.VDFTransclusionError):
            transcluder.transclude("foo")


class TestVDFTestTranscluder:

    def test_register(self, transcluder):
        transcluder.register("foo", "bar")
        assert "".join(transcluder.transclude("foo")) == "bar"

    def test_register_duplicate(self, transcluder):
        transcluder.register("foo", "bar")
        with pytest.raises(LookupError):
            transcluder.register("foo", "baz")

    def test_not_registered(self, transcluder):
        with pytest.raises(valve.vdf.VDFTransclusionError):
            "".join(transcluder.transclude("foo"))

    def test_unregister(self, transcluder):
        transcluder.register("foo", "bar")
        assert "".join(transcluder.transclude("foo")) == "bar"
        transcluder.unregister("foo")
        with pytest.raises(valve.vdf.VDFTransclusionError):
            "".join(transcluder.transclude("foo"))

    def test_unregister_not_registered(self, transcluder):
        with pytest.raises(LookupError):
            transcluder.unregister("foo")


class TestVDFObjectDecoder:

    def test_pair(self, transcluder):
        decoder = valve.vdf.VDFObjectDecoder(transcluder)
        decoder.on_key("foo")
        decoder.on_value("bar")
        assert decoder.object == {"foo": "bar"}

    def test_multiple_pairs(self, transcluder):
        decoder = valve.vdf.VDFObjectDecoder(transcluder)
        decoder.on_key("foo")
        decoder.on_value("bar")
        decoder.on_key("spam")
        decoder.on_value("eggs")
        assert decoder.object == {
            "foo": "bar",
            "spam": "eggs",
        }

    def test_nested_empty(self, transcluder):
        decoder = valve.vdf.VDFObjectDecoder(transcluder)
        decoder.on_key("foo")
        decoder.on_object_enter()
        decoder.on_object_exit()
        assert decoder.object == {"foo": {}}

    def test_nested(self, transcluder):
        decoder = valve.vdf.VDFObjectDecoder(transcluder)
        decoder.on_key("foo")
        decoder.on_object_enter()
        decoder.on_key("spam")
        decoder.on_value("eggs")
        decoder.on_object_exit()
        assert decoder.object == {
            "foo": {
                "spam": "eggs",
            },
        }

    def test_nested_multiple_pairs(self, transcluder):
        decoder = valve.vdf.VDFObjectDecoder(transcluder)
        decoder.on_key("foo")
        decoder.on_object_enter()
        decoder.on_key("spam")
        decoder.on_value("eggs")
        decoder.on_key("baz")
        decoder.on_value("qux")
        decoder.on_object_exit()
        assert decoder.object == {
            "foo": {
                "spam": "eggs",
                "baz": "qux",
            },
        }

    def test_nested_multiple(self, transcluder):
        decoder = valve.vdf.VDFObjectDecoder(transcluder)
        decoder.on_key("foo")
        decoder.on_object_enter()
        decoder.on_object_exit()
        decoder.on_key("bar")
        decoder.on_object_enter()
        decoder.on_object_exit()
        assert decoder.object == {
            "foo": {},
            "bar": {},
        }
