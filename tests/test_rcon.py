# -*- coding: utf-8 -*-

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import pytest
import six

import valve.source.rcon


class TestRCONMessage(object):

    def test_repr(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"foo")
        assert repr(message) == "<RCONMessage 0 RESPONSE_VALUE 3B>"

    def test_init_bytes(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"foo")
        assert message.id == 0
        assert isinstance(message.type, valve.source.rcon.RCONMessage.Type)
        assert message.body == b"foo"
        assert isinstance(message.body, six.binary_type)

    def test_init_unicode(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"foo".decode("ascii"))
        assert message.id == 0
        assert isinstance(message.type, valve.source.rcon.RCONMessage.Type)
        assert message.body == b"foo"
        assert isinstance(message.body, six.binary_type)

    def test_get_text(self):
        message = valve.source.rcon.RCONMessage(0, 0, "foo".encode("ascii"))
        assert message.text == "foo"
        assert isinstance(message.text, six.text_type)

    def test_get_text_bad(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"\xff")
        with pytest.raises(UnicodeDecodeError):
            getattr(message, "text")

    def test_set_text(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"")
        message.text = "foo"
        assert message.body == "foo".encode("ascii")
        assert isinstance(message.body, six.binary_type)

    def test_set_text_bad(self):
        message = valve.source.rcon.RCONMessage(0, 0, b"")
        with pytest.raises(UnicodeEncodeError):
            message.text = "\u00ff"

    def test_encode(self):
        message = valve.source.rcon.RCONMessage(0, 2, b"foo")
        encoded = message.encode()
        assert encoded == (
            b"\x0D\x00\x00\x00"  # Size; 4 + 4 + 3 + 2 = 0xD
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b"foo"               # Body
            b"\x00\x00"          # Terminators
        )
        assert isinstance(encoded, six.binary_type)

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
        assert isinstance(message.body, six.binary_type)
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


class TestResponseBuffer(object):

    def test_pop_empty(self):
        buffer_ = valve.source.rcon._ResponseBuffer()
        with pytest.raises(valve.source.rcon.RCONError):
            buffer_.pop()

    def test_feed_incomplete(self):
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.source.rcon._ResponseBuffer()
        buffer_.feed(auth_response[:5])
        buffer_.feed(auth_response[5:])
        message = buffer_.pop()
        assert message.id == 0
        assert message.type is message.Type.AUTH_RESPONSE
        assert message.body == b""
        assert isinstance(message.body, six.binary_type)

    def test_multi_part_response(self):
        part = (
            b"\x0D\x00\x00\x00"  # Size
            b"\x05\x00\x00\x00"  # ID
            b"\x00\x00\x00\x00"  # Type
            b"bar"               # Body
            b"\x00\x00"          # Terminators
        )
        empty = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x05\x00\x00\x00"  # ID
            b"\x00\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        terminator = (
            b"\x0E\x00\x00\x00"  # Size
            b"\x05\x00\x00\x00"  # ID
            b"\x00\x00\x00\x00"  # Type
            b"\x00\x01\x00\x00"  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.source.rcon._ResponseBuffer()
        buffer_.feed(part)
        buffer_.feed(part)
        buffer_.feed(empty)
        buffer_.feed(terminator)
        message = buffer_.pop()
        assert message.id == 5
        assert message.type is message.Type.RESPONSE_VALUE
        assert message.body == b"barbar"  # Black sheep ...
        assert isinstance(message.body, six.binary_type)

    def test_discard_before(self):
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.source.rcon._ResponseBuffer()
        buffer_.discard()
        buffer_.feed(auth_response)
        with pytest.raises(valve.source.rcon.RCONError):
            buffer_.pop()

    def test_discard_after(self):
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.source.rcon._ResponseBuffer()
        buffer_.feed(auth_response)
        assert len(buffer_._responses) == 1
        buffer_.discard()
        with pytest.raises(valve.source.rcon.RCONError):
            buffer_.pop()

    def test_clear(self):
        part = (
            b"\x0D\x00\x00\x00"  # Size
            b"\x05\x00\x00\x00"  # ID
            b"\x00\x00\x00\x00"  # Type
            b"bar"               # Body
            b"\x00\x00"          # Terminators
        )
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
            b"remainder"         # Remainder
        )
        buffer_ = valve.source.rcon._ResponseBuffer()
        buffer_.feed(part)
        buffer_.feed(auth_response)
        assert buffer_._buffer
        assert buffer_._partial_responses
        assert buffer_._responses
        buffer_.clear()
        assert buffer_._buffer == b""
        assert isinstance(buffer_._buffer, six.binary_type)
        assert buffer_._partial_responses == []
        assert buffer_._responses == []
        buffer_.discard()
        assert buffer_._discard_count == 1
        buffer_.clear()
        assert buffer_._discard_count == 0
