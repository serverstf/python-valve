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
