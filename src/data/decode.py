import struct
import sys
from array import array
from typing import BinaryIO

_TYPECODES = {
    1: "b",  # signed char (1 byte)
    2: "h",  # signed short (2 bytes)
    4: "l",  # signed long (4 bytes)
}


def rgb565(b: bytes | memoryview) -> int:
    raise NotImplementedError  # TODO: fix RGBA
    c = int.from_bytes(b[:2])
    return (
        ((c >> 11) & 0x1F)
        | (((c >> 5) & 0x3F) << 8)
        | ((c & 0x1F) << 16)
        | (0xFF << 24)
    )


def rgb888(b: bytes | memoryview) -> int:
    raise NotImplementedError  # TODO: fix RGBA
    c = int.from_bytes(b[:3])
    return (
        ((c >> 16) & 0xFF)
        | (((c >> 8) & 0xFF) << 8)
        | ((c & 0xFF) << 16)
        | (0xFF << 24)
    )


def argb8888(bs: bytes | memoryview) -> int:
    c = int.from_bytes(bs[:4], byteorder=sys.byteorder)
    return (
        (((c >> 16) & 0xFF) << 24)
        | (((c >> 8) & 0xFF) << 16)
        | ((c & 0xFF) << 8)
        | ((c >> 24) & 0xFF)
    )


# translated from /Common/util/compress.cpp
def rle(width: int, size, s: BinaryIO) -> bytes:
    tc = _TYPECODES[width]
    line = array(tc, [0] * size)
    fmt = f"={tc}"
    n = 0
    while n < size:
        b = s.read(1)
        if not b:
            break
        cx = struct.unpack("=b", b)[0]
        if cx == -128:
            cx = 0
        if cx < 0:
            run_len = 1 - cx
            ch = struct.unpack(fmt, s.read(width))[0]
            while run_len > 0:
                if n >= size:
                    raise IndexError("buffer overflow")
                line[n] = ch
                n += 1
                run_len -= 1
        else:
            seq_len = cx + 1
            while seq_len > 0:
                if n >= size:
                    raise IndexError("buffer overflow")
                line[n] = struct.unpack(fmt, s.read(width))[0]
                n += 1
                seq_len -= 1
    return line.tobytes()


def pack_bitmap(bm: list[int]) -> bytes:
    result = bytearray()
    for i in bm:
        result.extend(struct.pack(">L", i))
    return bytes(result)
