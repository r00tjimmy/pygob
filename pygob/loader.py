import struct

from .types import TypeID


class Loader:
    def load(self, buf):
        length, buf = self.decode_uint(buf)
        assert len(buf) == length

        typeid, buf = self.decode_int(buf)
        if typeid < 0:
            raise NotImplementedError("cannot decode non-standard type ID %d" %
                                      -typeid)
        typeid = TypeID(typeid)
        # TODO: why must we skip a zero byte here?
        value, buf = self.decode_value(typeid, buf[1:])
        return value

    def decode_bool(self, buf):
        n, buf = self.decode_uint(buf)
        return n == 1, buf

    def decode_uint(self, buf):
        (length, ) = struct.unpack('b', buf[:1])
        if length >= 0:  # small uint in a single byte
            return length, buf[1:]

        # larger uint split over multiple bytes
        length = -length
        n = 0
        for b in buf[1:length]:
            n = (n + b) << 8
        n += buf[length]
        return n, buf[length + 1:]

    def decode_int(self, buf):
        uint, buf = self.decode_uint(buf)
        if uint & 1:
            return ~(uint >> 1), buf
        else:
            return (uint >> 1), buf

    def decode_float(self, buf):
        n, buf = self.decode_uint(buf)
        rev = bytes(reversed(struct.pack('L', n)))
        (f, ) = struct.unpack('d', rev)
        return f, buf

    def decode_byte_slice(self, buf):
        count, buf = self.decode_uint(buf)
        return bytearray(buf[:count]), buf[count:]

    def decode_string(self, buf):
        count, buf = self.decode_uint(buf)
        # TODO: Go strings do not guarantee any particular encoding.
        # Add support for trying to decode the bytes using, say,
        # UTF-8, so we can return a real Python string.
        return buf[:count], buf[count:]

    def decode_complex(self, buf):
        re, buf = self.decode_float(buf)
        im, buf = self.decode_float(buf)
        return complex(re, im), buf

    def decode_value(self, typeid, buf):
        if typeid == TypeID.INT:
            return self.decode_int(buf)
        if typeid == TypeID.UINT:
            return self.decode_uint(buf)
        if typeid == TypeID.BOOL:
            return self.decode_bool(buf)
        if typeid == TypeID.FLOAT:
            return self.decode_float(buf)
        if typeid == TypeID.BYTE_SLICE:
            return self.decode_byte_slice(buf)
        if typeid == TypeID.STRING:
            return self.decode_string(buf)
        if typeid == TypeID.COMPLEX:
            return self.decode_complex(buf)
        raise NotImplementedError("cannot decode %s" % typeid)