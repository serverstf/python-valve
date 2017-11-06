# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

import struct
import io

from .util import Platform, ServerType
from .util import BrokenMessageError, BufferExhaustedError
from .byteio import ByteReader, ByteWriter


NO_SPLIT = -1
SPLIT = -2

A2S_PLAYER_REQUEST = 0x55
A2S_PLAYER_RESPONSE = 0x44
A2S_INFO_REQUEST = 0x54
A2S_INFO_RESPONSE = 0x49
A2S_RULES_REQUEST = 0x56
A2S_RULES_RESPONSE = 0x45
A2S_CHALLENGE_RESPONSE = 0x41

MASTER_SERVER_REQUEST = 0x31



class Message():

    @classmethod
    def decode(cls, packet):
        stream = io.BytesIO(packet)
        instance = cls()
        try:
            instance.read(stream)
        except struct.error as exc:
            raise BrokenMessageError(exc)
        return instance

    def encode(self):
        stream = io.BytesIO()
        try:
            self.write(stream)
        except struct.error as exc:
            raise BrokenMessageError(exc)
        return stream.getvalue()

    def _raise_unexpected(self, values):
        if values:
            raise TypeError("{} got an unexpected value {!r}".format(
                self.__class__.__name__, next(iter(values))))

    def _validate_response_type(self, response_type):
        if self.response_type != response_type:
            raise BrokenMessageError(
                "Invalid value ({}) for field 'response_type'".format(
                    self.response_type))


class Header(Message):

    def __init__(self, **values):
        if not values:
            return

        self.split = values.pop("split")
        if self.split not in [SPLIT, NO_SPLIT]:
            raise BrokenMessageError(
                "Invalid value ({}) for field 'split'".format(
                    self.split))
        self.payload = values.pop("payload", b"")

        self._raise_unexpected(values)

    def write(self, stream):
        writer = ByteWriter(stream, endian="<", encoding="utf-8")

        writer.write_int32(self.split)
        writer.write(self.payload)

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        self.split = reader.read_int32()
        self.payload = reader.read()


class Fragment(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        self.message_id = reader.read_int32()
        self.fragment_count = reader.read_uint8()
        self.fragment_id = reader.read_uint8()
        self.mtu = reader.read_int16()

        if self.is_compressed:
            self.decompressed_size = reader.read_int32()
            self.crc = reader.read_int32()

        self.payload = reader.read()

    @property
    def is_compressed(self):
        return bool(self.message_id & (1 << 16))


class InfoRequest(Message):
    def __init__(self, **values):
        self.request_type = values.pop("request_type", A2S_INFO_REQUEST)
        self.payload = values.pop("payload", "Source Engine Query")

        self._raise_unexpected(values)

    def write(self, stream):
        writer = ByteWriter(stream, endian="<", encoding="utf-8")

        writer.write_uint8(self.request_type)
        writer.write_cstring(self.payload)


class InfoResponse(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        self.response_type = reader.read_uint8()
        self._validate_response_type(A2S_INFO_RESPONSE)

        self.protocol = reader.read_uint8()
        self.server_name = reader.read_cstring()
        self.map = reader.read_cstring()
        self.folder = reader.read_cstring()
        self.game = reader.read_cstring()
        self.app_id = reader.read_uint16()
        self.player_count = reader.read_uint8()
        self.max_players = reader.read_uint8()
        self.bot_count = reader.read_uint8()
        self.server_type = ServerType(reader.read_uint8())
        self.platform = Platform(reader.read_uint8())
        self.password_protected = reader.read_bool()
        self.vac_enabled = reader.read_bool()
        self.version = reader.read_cstring()

        try:
            self.edf = reader.read_uint8()
        except BufferExhaustedError:
            self.edf = 0

        if self.edf & 0x80:
            self.port = reader.read_uint16()
        if self.edf & 0x10:
            self.steam_id = reader.read_uint64()
        if self.edf & 0x40:
            self.stv_port = reader.read_uint16()
            self.stv_name = reader.read_cstring()
        if self.edf & 0x20:
            self.keywords = reader.read_cstring()
        if self.edf & 0x01:
            self.game_id = reader.read_uint64()


class ChallengeResponse(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        self.response_type = reader.read_uint8()
        self._validate_response_type(A2S_CHALLENGE_RESPONSE)

        self.challenge = reader.read_int32()


class PlayersRequest(Message):
    def __init__(self, challenge, **values):
        self.request_type = values.pop("request_type", A2S_PLAYER_REQUEST)
        self.challenge = challenge

        self._raise_unexpected(values)

    def write(self, stream):
        writer = ByteWriter(stream, endian="<", encoding="utf-8")

        writer.write_uint8(self.request_type)
        writer.write_int32(self.challenge)


class PlayerEntry(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        self.index = reader.read_uint8()
        self.name = reader.read_cstring()
        self.score = reader.read_int32()
        self.duration = reader.read_float()


class PlayersResponse(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        self.response_type = reader.read_uint8()
        self._validate_response_type(A2S_PLAYER_RESPONSE)

        self.player_count = reader.read_uint8()
        self.players = []
        for player_num in range(self.player_count):
            player = PlayerEntry()
            player.read(stream)
            self.players.append(player)


class RulesRequest(Message):

    def __init__(self, challenge, **values):
        self.request_type = values.pop("request_type", A2S_RULES_REQUEST)
        self.challenge = challenge

        self._raise_unexpected(values)

    def write(self, stream):
        writer = ByteWriter(stream, endian="<", encoding="utf-8")

        writer.write_uint8(self.request_type)
        writer.write_int32(self.challenge)


class RulesResponse(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian="<", encoding="utf-8")

        # A2S_RESPONSE misteriously seems to add a FF FF FF FF
        # long to the beginning of the response which isn't
        # mentioned on the wiki.
        #
        # Behaviour witnessed with TF2 server 94.23.226.200:2045
        # As of 2015-11-22, Quake Live servers on steam do not
        if reader.peek(4) == b"\xFF\xFF\xFF\xFF":
            reader.read(4)

        self.response_type = reader.read_uint8()
        self._validate_response_type(A2S_RULES_RESPONSE)

        self.rule_count = reader.read_int16()
        self.rules = {}
        for rule_num in range(self.rule_count):
            name = reader.read_cstring()
            value = reader.read_cstring()
            self.rules[name] = value


class MasterServerRequest(Message):

    def __init__(self, region, address, filter_, **values):
        self.request_type = values.pop("request_type", MASTER_SERVER_REQUEST)
        self.region = region
        self.address = address
        self.filter = filter_

        self._raise_unexpected(values)

    def write(self, stream):
        writer = ByteWriter(stream, endian="<", encoding="utf-8")

        writer.write_uint8(self.request_type)
        writer.write_uint8(self.region)
        writer.write_cstring(self.address)
        writer.write_cstring(self.filter)


class MasterServerResponse(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian=">", encoding="utf-8")

        self.addresses = []
        while True:
            address = AddressEntry()
            try:
                address.read(stream)
            except BufferExhaustedError:
                break
            self.addresses.append(address)

        self.start_address = self.addresses.pop(0)


class AddressEntry(Message):

    def read(self, stream):
        reader = ByteReader(stream, endian=">", encoding="utf-8")

        self.host = reader.read_ip()
        self.port = reader.read_uint16()

    @property
    def is_null(self):
        return self.host == "0.0.0.0" and self.port == 0
