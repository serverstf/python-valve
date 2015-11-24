# -*- coding: utf-8 -*-
# Copyright (C) 2013 Oliver Ainsworth

from __future__ import (absolute_import,
                        unicode_literals, print_function, division)

import collections
import struct

import six

from . import util


NO_SPLIT = -1
SPLIT = -2


class BrokenMessageError(Exception):
    pass


class BufferExhaustedError(BrokenMessageError):

    def __init__(self, message="Incomplete message"):
        BrokenMessageError.__init__(self, message)


def use_default(func):
    def use_default(self, value=None, values={}):
        if value is None:
            return func(self, self.default_value, values)
        return func(self, value, values)
    return use_default


def needs_buffer(func):
    def needs_buffer(self, buffer, *args, **kwargs):
        if len(buffer) == 0:
            raise BufferExhaustedError
        return func(self, buffer, *args, **kwargs)
    return needs_buffer


class MessageField(object):

    fmt = None
    validators = []

    def __init__(self, name, optional=False,
                 default_value=None, validators=[]):
        """
            name -- used when decoding messages to set the key in the
                returned dictionary

            optional -- whether or not a field value must be provided
                when encoding

            default_value -- if optional is False, the value that is
                used if none is specified

            validators -- list of callables that return False if the
                value they're passed is invalid
        """

        if self.fmt is not None:
            if self.fmt[0] not in "@=<>!":
                self.format = "<" + self.fmt
            else:
                self.format = self.fmt
            if six.PY2:
                # Struct only accepts bytes
                self.format = self.format.encode("ascii")
        self.name = name
        self.optional = optional
        self._value = default_value
        self.validators = self.__class__.validators + validators

    @property
    def default_value(self):
        if self.optional:
            if self._value is not None:
                return self._value
        raise ValueError(
            "Field '{fname}' is not optional".format(fname=self.name))

    def validate(self, value):
        for validator in self.validators:
            try:
                if not validator(value):
                    raise ValueError
            except Exception:
                raise BrokenMessageError(
                    "Invalid value ({}) for field '{}'".format(
                        value, self.name))
        return value

    @use_default
    def encode(self, value, values={}):
        try:
            return struct.pack(self.format, self.validate(value))
        except struct.error as exc:
            raise BrokenMessageError(exc)

    @needs_buffer
    def decode(self, buffer, values={}):
        """
            Accepts a string of raw bytes which it will attempt to
            decode into some Python object which is returned. All
            remaining data left in the buffer is also returned which
            may be an empty string.

            Also acecpts a second argument which is a dictionary of the
            fields that have been decoded so far (i.e. occurs before
            this field in `fields` tuple). This allows the decoder to
            adapt it's funtionality based on the value of other fields
            if needs be.

            For example, in the case of A2S_PLAYER resposnes, the field
            `player_count` needs to be accessed at decode-time to determine
            how many player entries to attempt to decode.
        """

        field_size = struct.calcsize(self.format)
        if len(buffer) < field_size:
            raise BufferExhaustedError
        field_data = buffer[:field_size]
        left_overs = buffer[field_size:]
        try:
            return (self.validate(
                struct.unpack(self.format, field_data)[0]), left_overs)
        except struct.error as exc:
            raise BrokenMessageError(exc)


class ByteField(MessageField):
    fmt = "B"


class StringField(MessageField):
    fmt = "s"

    @use_default
    def encode(self, value, values={}):
        return value.encode("utf8") + b"\x00"

    @needs_buffer
    def decode(self, buffer, values={}):
        terminator = buffer.find(b"\x00")
        if terminator == -1:
            raise BufferExhaustedError("No string terminator")
        field_size = terminator + 1
        field_data = buffer[:field_size-1]
        left_overs = buffer[field_size:]
        return field_data.decode("utf8", "ignore"), left_overs


class ShortField(MessageField):
    fmt = "h"


class LongField(MessageField):
    fmt = "l"


class FloatField(MessageField):
    fmt = "f"


class PlatformField(ByteField):

    @needs_buffer
    def decode(self, buffer, values={}):
        byte, remnant_buffer = super(PlatformField,
                                     self).decode(buffer, values)
        return util.Platform(byte), remnant_buffer


class ServerTypeField(ByteField):

    @needs_buffer
    def decode(self, buffer, values={}):
        byte, remnant_buffer = super(ServerTypeField,
                                     self).decode(buffer, values)
        return util.ServerType(byte), remnant_buffer


class MessageArrayField(MessageField):
    """
        Represents a nested message within another message that is
        repeated a given number of time (often defined within the
        same message.)
    """

    def __init__(self, name, element, count=None):
        """
            element -- the Message subclass that will attempt to be decoded

            count -- ideally a callable that returns the number of
                'elements' to attempt to decode; count must also present
                a 'minimum' attribute which is minimum number of elements
                that must be decoded or else raise BrokenMessageError

                If count isn't callable (e.g. a number) it will be
                wrapped in a function with the minimum attribute set
                equal to the given 'count' value

                Helper static methods all(), value_of() and at_least()
                are provided which are intended to be used as the
                'count' argument, e.g.

                MessageArrayField("", SubMessage, MessageArrayField.all())

                ... will decode all SubMessages within the buffer
        """

        MessageField.__init__(self, name)
        if count is None:
            count = self.all()
        # Coerces the count argument to be a callable. For example,
        # in most cases count would be a Message.value_of(), however
        # if an integer is provided it will be wrapped in a lambda.
        self.count = count
        if not hasattr(count, "__call__"):

            def const_count(values={}):
                return count

            const_count.minimum = count
            self.count = const_count
        self.element = element

    def encode(self, elements, values={}):
        buf = []
        for i, element in enumerate(elements):
            if not isinstance(element, self.element):
                raise BrokenMessageError(
                    "Element {} ({}) is not instance of {}".format(
                        i, element, self.element.__name__))
            if i + 1 > self.count(values):
                raise BrokenMessageError("Too many elements")
            buf.append(element.encode())
        if len(buf) < self.count.minimum:
            raise BrokenMessageError("Too few elements")
        return b"".join(buf)

    def decode(self, buffer, values={}):
        entries = []
        count = 0
        while count < self.count(values):
            # Set start_buffer to the beginning of the buffer so that in
            # the case of buffer exhaustion it can return from the
            # start of the entry, not half-way through it.
            #
            # For example if you had the fields:
            #
            #       ComplexField =
            #           LongField
            #           ShortField
            #
            #       MessageArrayField(ComplexField,
            #                         count=MessageArrayField.all())
            #       ByteField()
            #
            # When attempting to decode the end of the buffer FF FF FF FF 00
            # the first four bytes will be consumed by LongField,
            # however ShortField will fail with BufferExhaustedError as
            # there's only one byte left. However, there is enough left
            # for the trailing ByteField. So when ComplexField
            # propagates ShortField's BufferExhaustedError the buffer will
            # only have the 00 byte remaining. The exception if caught
            # and buffer reverted to FF FF FF FF 00. This is passed
            # to ByteField which consumes one byte and the reamining
            # FF FF FF 00 bytes and stored as message payload.
            #
            # This is very much an edge case. :/
            start_buffer = buffer
            try:
                entry = self.element.decode(buffer)
                buffer = entry.payload
                entries.append(entry)
                count += 1
            except (BufferExhaustedError, BrokenMessageError) as exc:
                # Allow for returning 'at least something' if end of
                # buffer is reached.
                if count < self.count.minimum:
                    raise BrokenMessageError(exc)
                buffer = start_buffer
                break
        return entries, buffer

    @staticmethod
    def value_of(name):
        """
            Reference another field's value as the argument 'count'.
        """

        def field(values={}, f=None):
            f.minimum = values[name]
            return values[name]

        if six.PY3:
            field.__defaults__ = (field,)
        else:
            field.func_defaults = (field,)
        return field

    @staticmethod
    def all():
        """
            Decode as much as possible from the buffer.

            Note that if a full element field cannot be decoded it will
            return all entries decoded up to that point, and reset the
            buffer to the start of the entry which raised the
            BufferExhaustedError. So it is possible to have addtional
            fields follow a MessageArrayField and have
            count=MessageArrayField.all() as long as the size of the
            trailing fields < size of the MessageArrayField element.
        """

        i = [1]

        def all_(values={}):
            i[0] = i[0] + 1
            return i[0]

        all_.minimum = -1
        return all_

    @staticmethod
    def at_least(minimum):
        """
            Decode at least 'minimum' number of entries.
        """

        i = [1]

        def at_least(values={}):
            i[0] = i[0] + 1
            return i[0]

        at_least.minimum = minimum
        return at_least


class MessageDictField(MessageArrayField):
    """
        Decodes a series of key-value pairs from a message. Functionally
        identical to MessageArrayField except the results are returned as
        a dictionary instead of a list.
    """

    def __init__(self, name, key_field, value_field, count=None):
        """
            key_field and value_field are the respective components
            of the name-value pair that are to be decoded. The fields
            should have unique name strings. Tt is assumed that the
            key-field comes first, followed by the value.

            count is the same as MessageArrayField.
        """

        element = type("KeyValueField" if six.PY3 else b"KeyValueField",
                       (Message,), {"fields": (key_field, value_field)})
        self.key_field = key_field
        self.value_field = value_field
        MessageArrayField.__init__(self, name, element, count)

    def decode(self, buffer, values={}):
        entries, buffer = MessageArrayField.decode(self, buffer, values)
        entries_dict = {}
        for entry in entries:
            entries_dict[entry[
                self.key_field.name]] = entry[self.value_field.name]
        return entries_dict, buffer


class Message(collections.Mapping):

    fields = ()

    def __init__(self, payload=None, **field_values):
        self.fields = self.__class__.fields
        self.payload = payload
        self.values = field_values

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __delitem__(self, key):
        del self.values[key]

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def encode(self, **field_values):
        values = dict(self.values, **field_values)
        buf = []
        for field in self.fields:
            buf.append(field.encode(values.get(field.name, None), values))
        return b"".join(buf)

    @classmethod
    def decode(cls, packet):
        buffer = packet
        values = {}
        for field in cls.fields:
            values[field.name], buffer = field.decode(buffer, values)
        return cls(buffer, **values)


class Header(Message):

    fields = (
        LongField("split", validators=[lambda x: x in [SPLIT, NO_SPLIT]]),
    )


class Fragment(Message):

    fields = (
        LongField("message_id"),
        ByteField("fragment_count"),
        ByteField("fragment_id"),  # 0-indexed
        ShortField("mtu")
    )

    @property
    def is_compressed(self):
        return bool(self["message_id"] & 2**(2*8))


# TODO: FragmentCompressionData


class InfoRequest(Message):

    fields = (
        ByteField("request_type", True, 0x54),
        StringField("payload", True, "Source Engine Query")
    )


class InfoResponse(Message):

    fields = (
        ByteField("response_type", validators=[lambda x: x == 0x49]),
        ByteField("protocol"),
        StringField("server_name"),
        StringField("map"),
        StringField("folder"),
        StringField("game"),
        ShortField("app_id"),
        ByteField("player_count"),
        ByteField("max_players"),
        ByteField("bot_count"),
        ServerTypeField("server_type"),
        PlatformField("platform"),
        ByteField("password_protected"),  # BooleanField
        ByteField("vac_enabled"),  # BooleanField
        StringField("version")
        # TODO: EDF
    )


class GetChallengeResponse(Message):

    fields = (
        ByteField("response_type", validators=[lambda x: x == 0x41]),
        LongField("challenge")
    )


class PlayersRequest(Message):

    fields = (
        ByteField("request_type", True, 0x55),
        LongField("challenge")
    )


class PlayerEntry(Message):

    fields = (
        ByteField("index"),
        StringField("name"),
        LongField("score"),
        FloatField("duration")
    )


class PlayersResponse(Message):

    fields = (
        ByteField("response_type", validators=[lambda x: x == 0x44]),
        ByteField("player_count"),
        MessageArrayField("players",
                          PlayerEntry,
                          MessageArrayField.value_of("player_count"))
    )


class RulesRequest(Message):

    fields = (
        ByteField("request_type", True, 0x56),
        LongField("challenge")
    )


class RulesResponse(Message):

    fields = (
        ByteField("response_type", validators=[lambda x: x == 0x45]),
        ShortField("rule_count"),
        MessageDictField("rules",
                         StringField("key"),
                         StringField("value"),
                         MessageArrayField.value_of("rule_count"))
    )

    @classmethod
    def decode(cls, packet):
        # A2S_RESPONSE misteriously seems to add a FF FF FF FF
        # long to the beginning of the response which isn't
        # mentioned on the wiki.
        #
        # Behaviour witnessed with TF2 server 94.23.226.200:2045
        # As of 2015-11-22, Quake Live servers on steam do not
        if packet.startswith(b'\xff\xff\xff\xff'):
            packet = packet[4:]
        return super(cls, RulesResponse).decode(packet)

# For Master Server
class MSAddressEntryPortField(MessageField):
    fmt = "!H"


class MSAddressEntryIPField(MessageField):

    @needs_buffer
    def decode(self, buffer, values={}):
        if len(buffer) < 4:
            raise BufferExhaustedError
        field_data = buffer[:4]
        left_overs = buffer[4:]
        return (".".join(six.text_type(b) for b in
                struct.unpack(b"<BBBB", field_data)), left_overs)


class MasterServerRequest(Message):

    fields = (
        ByteField("request_type", True, 0x31),
        ByteField("region"),
        StringField("address"),
        StringField("filter")
    )


class MSAddressEntry(Message):

    fields = (
        MSAddressEntryIPField("host"),
        MSAddressEntryPortField("port")
    )

    @property
    def is_null(self):
        return self["host"] == "0.0.0.0" and self["port"] == 0


class MasterServerResponse(Message):

    fields = (
        # The first two fields are always FF FF FF FF and 66 0A
        # and can be ignored.
        MSAddressEntryIPField("start_host"),
        MSAddressEntryPortField("start_port"),
        MessageArrayField("addresses", MSAddressEntry, MessageArrayField.all())
    )
