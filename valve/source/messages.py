
import struct

from steam.servers import BrokenMessageError, SPLIT, NO_SPLIT

class BufferExhaustedError(BrokenMessageError):

    def __init__(self):
        BrokenMessageError.__init__(self, "Buffer has been exhausted; incomplete message")

def use_default(func):

    def use_default(self, value=None):

        if value is None:
            return func(self, self.default_value)

        return func(self, value)

    return use_default

def needs_buffer(func):

    def needs_buffer(self, buffer, values):
        if len(buffer) == 0:
            raise BufferExhaustedError

        return func(self, buffer, values)

    return needs_buffer

class MessageField(object):

    fmt = None
    validators = []

    def __init__(self, name, optional=False, default_value=None, validators=[]):
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

        if self.__class__.fmt is not None:
            if self.__class__.fmt[0] not in "@=<>!":
                self.format = "<" + self.__class__.fmt
            else:
                self.format = self.__class__.fmt

        self.name = name
        self.optional = optional
        self._value = default_value
        self.validators = self.__class__.validators + validators

    @property
    def default_value(self):
        if self.optional:
            if self._value is not None:
                return self._value

        raise ValueError("Field '{fname}' is not optional".format(fname=self.name))

    def validate(self, value):

        for validator in self.validators:
            if not validator(value):
                raise BrokenMessageError("Invalid value ({}) for field '{}'".format(value, self.name))

        return value

    @use_default
    def encode(self, value):
        return struct.pack(self.format, self.validate(value))

    @needs_buffer
    def decode(self, buffer, values):
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
            return self.validate(struct.unpack(self.format, field_data)[0]), left_overs
        except struct.error as exc:
            raise BrokenMessageError(exc)

class ByteField(MessageField):
    fmt = "B"

class StringField(MessageField):
    fmt = "s"

    @use_default
    def encode(self, value):
        return value.encode("utf8") + "\x00"

    @needs_buffer
    def decode(self, buffer, values):

        field_size = buffer.find("\x00") + 1
        field_data = buffer[:field_size-1]
        left_overs = buffer[field_size:]

        return field_data.decode("utf8", "ignore"), left_overs

class ShortField(MessageField):
    fmt = "h"

class LongField(MessageField):
    fmt = "l"

class FloatField(MessageField):
    fmt = "f"

class MessageArrayField(MessageField):
    """
        Represents a nested message within another message that is
        repeated a given number of time (often defined within the
        same message.)
    """

    def __init__(self, name, element, count):
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

        # Coerces the count argument to be a callable. For example,
        # in most cases count would be a Message.value_of(), however
        # if an integer is provided it will be wrapped in a lambda.

        self.count = count
        if not hasattr(count, "__call__"):

            def const_count(values):
                return count

            const_count.minimum = count
            self.count = const_count

        self.element = element

    def decode(self, buffer, values):

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
            #       MessageArrayField(ComplexField, count=MessageArrayField.all())
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
            # This is very much an edge cases. :/
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

        def field(values, f):
            f.minimum = values[name]
            return values[name]
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
        def all_(values):
            i[0] = i[0] + 1
            return i
        all_.minimum = -1

        return all_

    @staticmethod
    def at_least(minimum):
        """
            Decode at least 'minimum' number of entries.
        """

        i = [1]
        def at_least(values):
            i[0] = i[0] + 1
            return i
        at_least.minimum = minimum

        return at_least

class MessageDictField(MessageArrayField):
    """
        Decodes a series of key-value pairs from a message. Functionally
        identical to MessageArrayField except the results are returned as
        a dictionary instead of a list.
    """

    def __init__(self, name, key_field, value_field, count):
        """
            key_field and value_field are the respective components
            of the name-value pair that are to be decoded. The fields
            should have unique name strings. Tt is assumed that the
            key-field comes first, followed by the value.

            count is the same as MessageArrayField.
        """

        element = type("KeyValueField", (Message,), {"fields": (key_field, value_field)})
        self.key_field = key_field
        self.value_field = value_field

        MessageArrayField.__init__(self, name, element, count)

    def decode(self, buffer, values):
        entries, buffer = MessageArrayField.decode(self, buffer, values)

        entries_dict = {}
        for entry in entries:
            entries_dict[entry[self.key_field.name]] = entry[self.value_field.name]

        return entries_dict, buffer

class Message(object):

    fields = ()

    def __init__(self, payload=None, **field_values):

        self.fields = self.__class__.fields
        self.payload = payload
        self.values = field_values

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] == value

    def __delitem__(self, key):
        del self.values[key]

    def encode(self, **field_values):

        values = dict(self.values, **field_values)
        buffer = []
        for field in self.__class__.fields:
            buffer.append(field.encode(values.get(field.name, None)))

        return "".join(buffer)

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
                ByteField("fragment_id"), # 0-indexed
                ShortField("mtu"),
                )

    @property
    def is_compressed(self):
        return bool(self["message_id"] & 2**(2*8))

# TODO: FragmentCompressionData

class InfoRequest(Message):

    fields = (
                ByteField("request_type", True, 0x54),
                StringField("payload", True, "Source Engine Query"),
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
                ByteField("server_type"), # ServerField
                ByteField("platform"), # PlatformField
                ByteField("password_protected"), # BooleanField
                ByteField("vac_enabled"), # BooleanField
                StringField("version"),
                # TODO: EDF
                )

class GetChallengeRequest(Message):

    fields = (
                ByteField("request_type", True, 0x57),
                )

class GetChallengeResponse(Message):

    fields = (
                ByteField("response_type", validators=[lambda x: x == 0x41]),
                LongField("challenge"),
                )

class PlayersRequest(Message):

    fields = (
                ByteField("request_type", True, 0x55),
                LongField("challenge"),
                )

class PlayerEntry(Message):

    fields = (
                ByteField("index"),
                StringField("name"),
                LongField("score"),
                FloatField("duration"),
                )

class PlayersResponse(Message):

    fields = (
                ByteField("response_type", validators=[lambda x: x == 0x44]),
                ByteField("player_count"),
                MessageArrayField("players", PlayerEntry, MessageArrayField.value_of("player_count")),
                )

class RulesRequest(Message):

    fields = (
                ByteField("request_type", True, 0x56),
                LongField("challenge")
                )

class RulesResponse(Message):

    fields = (
                # A2S_RESPONSE misteriously seems to add a FF FF FF FF
                # long to the beginning of the response which isn't
                # mentioned on the wiki.
                #
                # Behaviour witnessed with TF2 server 94.23.226.200:2045
                LongField("long"),

                ByteField("response_type", validators=[lambda x: x == 0x45]),
                ShortField("rule_count"),
                MessageDictField("rules", StringField("key"), StringField("value"), MessageArrayField.value_of("rule_count")),
                )

class PingRequest(Message):

    fields = (
                ByteField("request_type", True, 0x69),
                )

class PingResponse(Message):

    fields = (
                ByteField("response_type", validators=[lambda x: x == 0x6a]),
                StringField("payload", validators=[lambda x: x == "00000000000000"]),
                )

# For Master Server
class MSAddressEntryPortField(MessageField):
    fmt = "!H"

class MSAddressEntryIPField(MessageField):

    @needs_buffer
    def decode(self, buffer, values):

        if len(buffer) < 4:
            raise BufferExhaustedError

        field_data = buffer[:4]
        left_overs = buffer[4:]

        return ".".join(str(b) for b in struct.unpack("<BBBB", field_data)), left_overs

class MasterServerRequest(Message):

    fields = (
                ByteField("request_type", True, 0x31),
                ByteField("region"),
                StringField("address"),
                StringField("filter"),
                )

class MSAddressEntry(Message):

    fields = (
                MSAddressEntryIPField("host"),
                MSAddressEntryPortField("port"),
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
                MessageArrayField("addresses", MSAddressEntry, MessageArrayField.all()),
                )
