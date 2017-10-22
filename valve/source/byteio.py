import struct
import io

class ByteReader(object):
    def __init__(self, stream, endian='='):
        self.stream = stream
        self.endian = endian

    def read(self, *args):
        return self.stream.read(*args)

    def unpack(self, fmt):
        fmt = self.endian + fmt
        fmt_size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.stream.read(fmt_size))

    def unpack_one(self, fmt):
        values = self.unpack(fmt)
        assert len(values) == 1
        return values[0]

    def read_char(self):
        return self.unpack_one("c")

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

    def read_cstring(self, charsize=1):
        string = b""
        while True:
            c = self.read(charsize)
            if int.from_bytes(c, "little") == 0:
                break
            else:
                string += c
        return string

    def read_vec3(self):
        return self.unpack("4f")

    def read_vec4(self):
        return self.unpack("4f")

    def read_vec3x3(self):
        return (self.read_vec3() for i in range(3))

    def read_vec4x4(self):
        return (self.read_vec4() for i in range(4))

    def read_bool(self):
        return bool(self.unpack("b"))

    def align(self, num):
        current_pos = self.stream.tell()
        align_bytes = num - (current_pos % num)
        if align_bytes != num:
            self.stream.seek(align_bytes, io.SEEK_CUR)


class ByteWriter(object):
    def __init__(self, stream, endian='='):
        self.stream = stream
        self.endian = endian

    def write(self, *args):
        return self.stream.write(*args)

    def pack(self, fmt, *values):
        fmt = self.endian + fmt
        fmt_size = struct.calcsize(fmt)
        return self.stream.write(struct.pack(fmt, *values))

    def write_char(self, val):
        self.pack("c", val)

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

    def write_vec3(self, val):
        self.pack("4f", *val)

    def write_vec4(self, val):
        self.pack("4f", *val)

    def write_vec3x3(self, val):
        for vec in val:
            self.write_vec3(vec)

    def write_vec4x4(self, val):
        for vec in val:
            self.write_vec4(vec)

    def write_bool(self, val):
        self.pack("b", val)

    def align(self, num):
        current_pos = self.stream.tell()
        align_bytes = num - (current_pos % num)
        if align_bytes != num:
            self.stream.seek(align_bytes, io.SEEK_CUR)
