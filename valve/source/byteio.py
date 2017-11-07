# -*- coding: utf-8 -*-
# Copyright (C) 2017 Oliver Ainsworth

import struct
import io

from .util import BufferExhaustedError



class ByteReader():
    def __init__(self, stream, endian="=", encoding=None):
        self.stream = stream
        self.endian = endian
        self.encoding = encoding

    def read(self, size=-1):
        data = self.stream.read(size)
        if size > -1 and len(data) != size:
            raise BufferExhaustedError()

        return data

    def peek(self, size=-1):
        cur_pos = self.stream.tell()
        data = self.stream.read(size)
        self.stream.seek(cur_pos, io.SEEK_SET)
        return data

    def unpack(self, fmt):
        fmt = self.endian + fmt
        fmt_size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.read(fmt_size))

    def unpack_one(self, fmt):
        values = self.unpack(fmt)
        assert len(values) == 1
        return values[0]

    def read_int8(self):
        return self.unpack_one("b")

    def read_uint8(self):
        return self.unpack_one("B")

    def read_int16(self):
        return self.unpack_one("h")

    def read_uint16(self):
        return self.unpack_one("H")

    def read_int32(self):
        return self.unpack_one("l")

    def read_uint32(self):
        return self.unpack_one("L")

    def read_int64(self):
        return self.unpack_one("q")

    def read_uint64(self):
        return self.unpack_one("Q")

    def read_float(self):
        return self.unpack_one("f")

    def read_double(self):
        return self.unpack_one("d")

    def read_bool(self):
        return bool(self.unpack("b"))

    def read_char(self):
        char = self.unpack_one("c")
        if self.encoding is not None:
            return char.decode(self.encoding)
        else:
            return char

    def read_cstring(self, charsize=1):
        string = b""
        while True:
            c = self.read(charsize)
            if int.from_bytes(c, "little") == 0:
                break
            else:
                string += c

        if self.encoding is not None:
            return string.decode(self.encoding)
        else:
            return string

    def read_ip(self):
        return ".".join(str(o) for o in self.unpack("BBBB"))


class ByteWriter():
    def __init__(self, stream, endian="=", encoding=None):
        self.stream = stream
        self.endian = endian
        self.encoding = encoding

    def write(self, *args):
        return self.stream.write(*args)

    def pack(self, fmt, *values):
        fmt = self.endian + fmt
        fmt_size = struct.calcsize(fmt)
        return self.stream.write(struct.pack(fmt, *values))

    def write_int8(self, val):
        self.pack("b", val)

    def write_uint8(self, val):
        self.pack("B", val)

    def write_int16(self, val):
        self.pack("h", val)

    def write_uint16(self, val):
        self.pack("H", val)

    def write_int32(self, val):
        self.pack("l", val)

    def write_uint32(self, val):
        self.pack("L", val)

    def write_int64(self, val):
        self.pack("q", val)

    def write_uint64(self, val):
        self.pack("Q", val)

    def write_float(self, val):
        self.pack("f", val)

    def write_double(self, val):
        self.pack("d", val)

    def write_bool(self, val):
        self.pack("b", val)

    def write_char(self, val):
        if self.encoding is not None:
            self.pack("c", val.encode(self.encoding))
        else:
            self.pack("c", val)

    def write_cstring(self, val):
        if self.encoding is not None:
            self.write(val.encode(self.encoding) + b"\x00")
        else:
            self.write(val + b"\x00")
