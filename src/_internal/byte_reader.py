import io
import struct
from typing import BinaryIO, ClassVar, Literal


class ByteReader:
    type Endian = Literal["big", "little", "native"]
    _ENDIAN_TO_BO: ClassVar[dict[ByteReader.Endian, str]] = {
        "big": ">",
        "little": "<",
        "native": "-",
    }

    def __init__(
        self,
        stream: BinaryIO,
        endian: ByteReader.Endian = "little",
        encoding: str = "latin-1",
    ) -> None:
        self.stream = stream
        self.endian = endian
        self.encoding = encoding

        bo = self._ENDIAN_TO_BO[self.endian]
        self._fi8 = f"{bo}b"
        self._fu8 = f"{bo}B"
        self._fi16 = f"{bo}h"
        self._fu16 = f"{bo}H"
        self._fi32 = f"{bo}i"
        self._fu32 = f"{bo}I"
        self._fi64 = f"{bo}q"
        self._fu64 = f"{bo}Q"
        self._ff32 = f"{bo}f"
        self._ff64 = f"{bo}d"

    def read(self, size: int = -1) -> bytes:
        return self.stream.read(size)

    def tell(self) -> int:
        return self.stream.tell()

    def skip(self, size: int) -> None:
        self.stream.seek(size, io.SEEK_CUR)

    def seek(self, to: int, whence: int = io.SEEK_SET) -> None:
        self.stream.seek(to, whence)

    def peek(self, size: int = 0) -> bytes:
        pos = self.stream.tell()
        data = self.stream.read(size)
        self.stream.seek(pos)
        return data

    def byte(self) -> int:
        return self.stream.read(1)[0]

    def i8(self) -> int:
        v = self.stream.read(1)
        return struct.unpack(self._fi8, v)[0]

    def u8(self) -> int:
        v = self.stream.read(1)
        return struct.unpack(self._fu8, v)[0]

    def i16(self) -> int:
        v = self.stream.read(2)
        return struct.unpack(self._fi16, v)[0]

    def u16(self) -> int:
        v = self.stream.read(2)
        return struct.unpack(self._fu16, v)[0]

    def i32(self) -> int:
        v = self.stream.read(4)
        return struct.unpack(self._fi32, v)[0]

    def u32(self) -> int:
        v = self.stream.read(4)
        return struct.unpack(self._fu32, v)[0]

    def i64(self) -> int:
        v = self.stream.read(8)
        return struct.unpack(self._fi64, v)[0]

    def u64(self) -> int:
        v = self.stream.read(8)
        return struct.unpack(self._fu64, v)[0]

    def f32(self) -> float:
        v = self.stream.read(4)
        return struct.unpack(self._ff32, v)[0]

    def f64(self) -> float:
        v = self.stream.read(8)
        return struct.unpack(self._ff64, v)[0]

    def cstr(self, encoding: str | None = None) -> str:
        data = bytearray()
        while True:
            b = self.byte()
            if b == 0:
                break
            data.append(b)
        return bytes(data).decode(encoding or self.encoding)

    # Pascal string (length prefixed)
    def pstr(self, encoding: str | None = None, strip: bool = True) -> str:
        l = self.u32()
        data = self.stream.read(l)
        if strip:
            data = data.rstrip(b"\x00")
        return data.decode(encoding or self.encoding)

    # fixed size string
    def fstr(self, size: int, encoding: str | None = None, strip: bool = True) -> str:
        data = self.stream.read(size)
        if strip:
            data = data.rstrip(b"\x00")
        return data.decode(encoding or self.encoding)
