# -*- coding: utf-8 -*-

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import argparse
import textwrap

import docopt
import pytest
import six

import valve.rcon


class TestRCONMessage(object):

    def test_repr(self):
        message = valve.rcon.RCONMessage(0, 0, b"foo")
        assert repr(message) == "<RCONMessage 0 RESPONSE_VALUE 3B>"

    def test_init_bytes(self):
        message = valve.rcon.RCONMessage(0, 0, b"foo")
        assert message.id == 0
        assert isinstance(message.type, valve.rcon.RCONMessage.Type)
        assert message.body == b"foo"
        assert isinstance(message.body, six.binary_type)

    def test_init_unicode(self):
        message = valve.rcon.RCONMessage(0, 0, b"foo".decode("ascii"))
        assert message.id == 0
        assert isinstance(message.type, valve.rcon.RCONMessage.Type)
        assert message.body == b"foo"
        assert isinstance(message.body, six.binary_type)

    def test_get_text(self):
        message = valve.rcon.RCONMessage(0, 0, "foo".encode("ascii"))
        assert message.text == "foo"
        assert isinstance(message.text, six.text_type)

    def test_get_text_bad(self):
        message = valve.rcon.RCONMessage(0, 0, b"\xff")
        with pytest.raises(UnicodeDecodeError):
            getattr(message, "text")

    def test_set_text(self):
        message = valve.rcon.RCONMessage(0, 0, b"")
        message.text = "foo"
        assert message.body == "foo".encode("ascii")
        assert isinstance(message.body, six.binary_type)

    def test_set_text_bad(self):
        message = valve.rcon.RCONMessage(0, 0, b"")
        with pytest.raises(UnicodeEncodeError):
            message.text = "\u00ff"

    def test_encode(self):
        message = valve.rcon.RCONMessage(0, 2, b"foo")
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
        message, remainder = valve.rcon.RCONMessage.decode(
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
        with pytest.raises(valve.rcon.RCONMessageError):
            valve.rcon.RCONMessage.decode(buffer_)

    def test_decode_incomplete(self):
        with pytest.raises(valve.rcon.RCONMessageError):
            valve.rcon.RCONMessage.decode(b"\xFF\x00\x00\x00")


class TestResponseBuffer(object):

    def test_pop_empty(self):
        buffer_ = valve.rcon._ResponseBuffer()
        with pytest.raises(valve.rcon.RCONError):
            buffer_.pop()

    def test_feed_incomplete(self):
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.rcon._ResponseBuffer()
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
        buffer_ = valve.rcon._ResponseBuffer()
        buffer_.feed(part)
        buffer_.feed(part)
        buffer_.feed(empty)
        buffer_.feed(terminator)
        message = buffer_.pop()
        assert message.id == 5
        assert message.type is message.Type.RESPONSE_VALUE
        assert message.body == b"barbar"  # Black sheep ...
        assert isinstance(message.body, six.binary_type)

    def test_single_part_response(self):
        part = (
            b"\x0D\x00\x00\x00"  # Size
            b"\x05\x00\x00\x00"  # ID
            b"\x00\x00\x00\x00"  # Type
            b"bar"               # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.rcon._ResponseBuffer(False)
        buffer_.feed(part)
        buffer_.feed(part)
        message = buffer_.pop()
        assert message.id == 5
        assert message.type is message.Type.RESPONSE_VALUE
        assert message.body == b"bar"  # Black sheep ...
        assert isinstance(message.body, six.binary_type)

    def test_discard_before(self):
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.rcon._ResponseBuffer()
        buffer_.discard()
        buffer_.feed(auth_response)
        with pytest.raises(valve.rcon.RCONError):
            buffer_.pop()

    def test_discard_after(self):
        auth_response = (
            b"\x0A\x00\x00\x00"  # Size
            b"\x00\x00\x00\x00"  # ID
            b"\x02\x00\x00\x00"  # Type
            b""                  # Body
            b"\x00\x00"          # Terminators
        )
        buffer_ = valve.rcon._ResponseBuffer()
        buffer_.feed(auth_response)
        assert len(buffer_._responses) == 1
        buffer_.discard()
        with pytest.raises(valve.rcon.RCONError):
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
        buffer_ = valve.rcon._ResponseBuffer()
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


class TestRCON(object):

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_authenticate(self, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.AUTH, b"password")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.AUTH_RESPONSE, b"")
        rcon = valve.rcon.RCON(rcon_server.server_address, b"password")
        with rcon as rcon:
            assert rcon.authenticated is True

    def test_authenticate_not_connected(self):
        rcon = valve.rcon.RCON(None, b"")
        with pytest.raises(valve.rcon.RCONError):
            rcon.authenticate()

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_authenticate_wrong_password(self, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.AUTH, b"")
        e_request.respond(
            -1, valve.rcon.RCONMessage.Type.AUTH_RESPONSE, b"")
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        with pytest.raises(valve.rcon.RCONAuthenticationError) as exc:
            with rcon as rcon:
                pass
            assert rcon.authenticated is True
            assert exc.value.banned is False

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_authenticate_banned(self, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.AUTH, b"password")
        e_request.respond_close()
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        with pytest.raises(valve.rcon.RCONAuthenticationError) as exc:
            with rcon as rcon:
                pass
            assert rcon.authenticated is True
            assert exc.value.banned is True

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_authenticate_timeout(self, request, rcon_server):
        rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.AUTH, b"")
        rcon = valve.rcon.RCON(rcon_server.server_address, b"", 1.5)
        rcon.connect()
        request.addfinalizer(rcon.close)
        with pytest.raises(valve.rcon.RCONTimeoutError):
            rcon.authenticate()

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_execute(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        e_request.respond_terminate_multi_part(0)
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        response = rcon.execute("echo hello")
        assert response.id == 0
        assert response.type is response.Type.RESPONSE_VALUE
        assert response.body == b"hello"
        assert isinstance(response.body, six.binary_type)

    def test_execute_not_connected(self):
        rcon = valve.rcon.RCON(None, b"")
        with pytest.raises(valve.rcon.RCONError):
            rcon.execute("foo")

    def test_execute_not_authenticated(self, request, rcon_server):
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        request.addfinalizer(rcon.close)
        with pytest.raises(valve.rcon.RCONError):
            rcon.execute("foo")

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_execute_no_block(self, request, rcon_server):
        e1_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e1_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        e1_request.respond_terminate_multi_part(0)
        rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        e2_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e2_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        e2_request.respond_terminate_multi_part(0)
        rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        response_1 = rcon.execute("echo hello", block=False)
        response_2 = rcon.execute("echo hello", block=True)
        assert response_1 is None
        assert response_2.id == 0
        assert response_2.type is response_2.Type.RESPONSE_VALUE
        assert response_2.body == b"hello"
        assert isinstance(response_2.body, six.binary_type)

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_execute_timeout(self, request, rcon_server):
        rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"")
        rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        rcon = valve.rcon.RCON(rcon_server.server_address, b"", 1.5)
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        with pytest.raises(valve.rcon.RCONTimeoutError):
            rcon.execute("")

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_call(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        e_request.respond_terminate_multi_part(0)
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        response = rcon("echo hello")
        assert response == "hello"
        assert isinstance(response, six.text_type)

    def test_call_no_multi_timeout(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        rcon = valve.rcon.RCON(
            rcon_server.server_address, b"", timeout=3)
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        with pytest.raises(valve.rcon.RCONTimeoutError):
            rcon("echo hello")

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_call_no_multi(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        rcon = valve.rcon.RCON(
            rcon_server.server_address, b"", multi_part=False)
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        response = rcon("echo hello")
        assert response == "hello"
        assert isinstance(response, six.text_type)

    def test_call_not_connected(self):
        rcon = valve.rcon.RCON(None, b"")
        with pytest.raises(valve.rcon.RCONError):
            rcon("foo")

    def test_call_not_authenticated(self, request, rcon_server):
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        request.addfinalizer(rcon.close)
        with pytest.raises(valve.rcon.RCONError):
            rcon("foo")

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_call_text_bad(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"\xFF")
        e_request.respond_terminate_multi_part(0)
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        with pytest.raises(valve.rcon.RCONMessageError):
            rcon("")

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_cvarlist(self, request, rcon_server):
        cvarlist = textwrap.dedent("""
        cvar list
        --------------
        foo                   : cmd      : , "a", "sv" : foo-description
        bar                   : 5        :             : bar-description
        --------------
        2345 total convars/concommands
        """)
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"cvarlist")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, cvarlist)
        e_request.respond_terminate_multi_part(0)
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        convars = list(rcon.cvarlist())
        assert len(convars) == 2
        assert convars[0].name == "foo"
        assert convars[0].value == "cmd"
        assert convars[0].flags == frozenset({"a", "sv"})
        assert isinstance(convars[0].flags, frozenset)
        assert convars[0].description == "foo-description"
        assert convars[1].name == "bar"
        assert convars[1].value == "5"
        assert convars[1].flags == frozenset({})
        assert isinstance(convars[1].flags, frozenset)
        assert convars[1].description == "bar-description"

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_cvarlist_text_bad(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"cvarlist")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"\xFF")
        e_request.respond_terminate_multi_part(0)
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        assert list(rcon.cvarlist()) == []

    @pytest.mark.timeout(timeout=3, method="thread")
    def test_cvarlist_malformed(self, request, rcon_server):
        e_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"cvarlist")
        e_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"asdf")
        e_request.respond_terminate_multi_part(0)
        rcon = valve.rcon.RCON(rcon_server.server_address, b"")
        rcon.connect()
        rcon._authenticated = True
        request.addfinalizer(rcon.close)
        assert list(rcon.cvarlist()) == []


class TestExecute(object):

    def test(self, rcon_server):
        e1_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.AUTH, b"password")
        e1_request.respond(
            0, valve.rcon.RCONMessage.Type.AUTH_RESPONSE, b"")
        e2_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e2_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"")
        e2_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        e2_request.respond_terminate_multi_part(0)
        response = valve.rcon.execute(
            rcon_server.server_address, "password", "echo hello")
        assert response == "hello"
        assert isinstance(response, six.text_type)

    def test_no_multi(self, rcon_server):
        e1_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.AUTH, b"password")
        e1_request.respond(
            0, valve.rcon.RCONMessage.Type.AUTH_RESPONSE, b"")
        e2_request = rcon_server.expect(
            0, valve.rcon.RCONMessage.Type.EXECCOMMAND, b"echo hello")
        e2_request.respond(
            0, valve.rcon.RCONMessage.Type.RESPONSE_VALUE, b"hello")
        response = valve.rcon.execute(
            rcon_server.server_address, "password", "echo hello", False)
        assert response == "hello"
        assert isinstance(response, six.text_type)


class TestConVar(object):

    def test_repr(self):
        assert repr(valve.rcon.ConVar(
            "foo", "bar", frozenset(), "")) == "<ConVar 'foo' = 'bar'>"


class TestParseAddress(object):

    def test(self):
        assert valve.rcon._parse_address(
            "localhost:9001") == ("localhost", 9001)

    def test_port_default(self):
        assert valve.rcon._parse_address("localhost") == ("localhost", 27015)

    def test_port_not_a_number(self):
        with pytest.raises(ValueError):
            valve.rcon._parse_address("localhost:asdf")

    def test_port_too_small(self):
        with pytest.raises(ValueError):
            valve.rcon._parse_address("localhost:0")

    def test_port_too_big(self):
        with pytest.raises(ValueError):
            valve.rcon._parse_address("localhost:65536")


class TestShell(object):

    def test_address_and_password(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "_RCONShell", pytest.Mock())
        shell = valve.rcon._RCONShell.return_value
        valve.rcon.shell(("localhost", "9001"), "password")
        assert shell.onecmd.call_args[0] == (
            "!connect localhost:9001 password",)
        assert shell.cmdloop.called

    def test_address_only(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "_RCONShell", pytest.Mock())
        shell = valve.rcon._RCONShell.return_value
        valve.rcon.shell(("localhost", "9001"))
        assert shell.onecmd.call_args[0] == ("!connect localhost:9001 ",)
        assert shell.cmdloop.called

    def test_no_address(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "_RCONShell", pytest.Mock())
        shell = valve.rcon._RCONShell.return_value
        valve.rcon.shell()
        assert not shell.onecmd.called
        assert shell.cmdloop.called

    def test_password_only(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "_RCONShell", pytest.Mock())
        shell = valve.rcon._RCONShell.return_value
        valve.rcon.shell(password="password")
        assert not shell.onecmd.called
        assert shell.cmdloop.called

    def test_ignore_interrupt(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "_RCONShell", pytest.Mock())
        shell = valve.rcon._RCONShell.return_value
        shell.cmdloop.side_effect = KeyboardInterrupt
        valve.rcon.shell()
        assert shell.cmdloop.called


class TestMain(object):

    @pytest.fixture
    def shell(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "shell", pytest.Mock())
        return valve.rcon.shell

    @pytest.fixture
    def execute(self, monkeypatch):
        monkeypatch.setattr(valve.rcon, "execute", pytest.Mock())
        return valve.rcon.execute

    def test_no_arguments(self, shell, execute):
        valve.rcon._main([])
        assert shell.called
        assert not execute.called
        assert shell.call_args[0] == (None, None, True)

    def test_address_only(self, shell, execute):
        valve.rcon._main(["localhost:9001"])
        assert shell.called
        assert not execute.called
        assert shell.call_args[0] == (("localhost", 9001), None, True)

    def test_address_and_password(self, shell, execute):
        valve.rcon._main(["localhost:9001", "-p", "password"])
        assert shell.called
        assert not execute.called
        assert shell.call_args[0] == (("localhost", 9001), "password", True)

    def test_address_and_password_and_no_multi(self, shell, execute):
        valve.rcon._main(["localhost:9001", "-p", "password", "-n"])
        assert shell.called
        assert not execute.called
        assert shell.call_args[0] == (("localhost", 9001), "password", False)

    def test_password_only(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["-p", "password"])
        assert not shell.called
        assert not execute.called

    def test_no_multi_only(self, shell, execute):
        valve.rcon._main(["-n"])
        assert shell.called
        assert not execute.called
        assert shell.call_args[0] == (None, None, False)

    def test_execute(self, capsys, shell, execute):
        execute.return_value = "command output"
        valve.rcon._main(["localhost:9001", "-p", "password", "-e", "foo"])
        assert not shell.called
        assert execute.called
        assert execute.call_args[0] == (
            ("localhost", 9001), "password", "foo", True
        )
        assert capsys.readouterr()[0] == "command output\n"

    def test_execute_no_multi(self, capsys, shell, execute):
        execute.return_value = "command output"
        valve.rcon._main(["localhost:9001", "-p", "password", "-n", "-e", "foo"])
        assert not shell.called
        assert execute.called
        assert execute.call_args[0] == (
            ("localhost", 9001), "password", "foo", False
        )
        assert capsys.readouterr()[0] == "command output\n"

    def test_execute_no_address(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["-p", "password", "-e", "foo"])
        assert not shell.called
        assert not execute.called

    def test_execute_no_address_no_multi(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["-p", "password", "-n", "-e", "foo"])
        assert not shell.called
        assert not execute.called

    def test_execute_no_password(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["localhost:9001", "-e", "foo"])
        assert not shell.called
        assert not execute.called

    def test_execute_no_password_no_multi(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["localhost:9001", "-n", "-e", "foo"])
        assert not shell.called
        assert not execute.called

    def test_execute_no_address_or_password(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["-e", "foo"])
        assert not shell.called
        assert not execute.called

    def test_execute_no_address_or_password_no_multi(self, shell, execute):
        with pytest.raises(docopt.DocoptExit):
            valve.rcon._main(["-n", "-e", "foo"])
        assert not shell.called
        assert not execute.called
