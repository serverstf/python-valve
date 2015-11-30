# -*- coding: utf-8 -*-

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import pytest

import valve.source.rcon


class TestRCONMessage(object):

    def test_init_bytes(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"foo")
        assert message.id == 0
        assert isinstance(message.type, valve.source.rcon.RCONMessage.Type)
        assert message.body == b"foo"

    def test_init_unicode(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"foo".decode("ascii"))
        assert message.id == 0
        assert isinstance(message.type, valve.source.rcon.RCONMessage.Type)
        assert message.body == b"foo"

    def test_get_text(self):
        message = valve.source.rcon.RCONMessage(0, 0, "foo".encode("ascii"))
        assert message.text == "foo"

    def test_get_text_bad(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"\xff")
        with pytest.raises(UnicodeDecodeError):
            getattr(message, "text")

    def test_set_text(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"")
        message.text = "foo"
        assert message.body == "foo".encode("ascii")

    def test_set_text_bad(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"")
        with pytest.raises(UnicodeEncodeError):
            message.text = "\u00ff"

    def test_encode(self):
        message = valve.source.rcon.RCONMessage(0, 2, b"foo")
        assert message.encode() == (
            b"\x0D\x00\x00\x00"  # Size; 4 + 4 + 3 + 2 = 0xD
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b"foo"               # Body
            b"\x00\x00"          # Terminators
        )

    def test_decode(self):
        message, remainder = valve.source.rcon.RCONMessage.decode(
            b"\x0D\x00\x00\x00"          # Size
            b"\x00\x00\x00\x00"          # ID
            b"\x02\x00\x00\x00"          # Type
            b"foo"                       # Body
            b"\x00\x00"                  # Terminators
            b"\xAA\xBB\xCC\xDD\xEE\xFF"  # Remainder
        )
        assert message.id == 0
        assert message.type == 2
        assert isinstance(message.type, message.Type)
        assert message.body == b"foo"
        assert remainder == b"\xAA\xBB\xCC\xDD\xEE\xFF"

    @pytest.mark.parametrize("buffer_", [
        b"",
        b"\x00",
        b"\x00\x00",
        b"\x00\x00\x00",
    ])
    def test_decode_too_short(self, buffer_):
        with pytest.raises(valve.source.rcon.RCONMessageError):
            valve.source.rcon.RCONMessage.decode(buffer_)

    def test_decode_incomplete(self):
        with pytest.raises(valve.source.rcon.RCONMessageError):
            valve.source.rcon.RCONMessage.decode(b"\xFF\x00\x00\x00")
