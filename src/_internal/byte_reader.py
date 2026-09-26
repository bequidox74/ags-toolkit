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
        encoding: str = "utf-8",
    ) -> None:
        self.stream = stream
        self.endian = endian
        self.encoding = encoding
        self._bo = self._ENDIAN_TO_BO[self.endian]

    def read(self, size: int = -1) -> bytes:
        return self.stream.read(size)

    def tell(self) -> int:
        return self.stream.tell()

    def skip(self, size: int) -> None:
        self.stream.seek(size, io.SEEK_CUR)

    def byte(self) -> int:
        return self.stream.read(1)[0]

    def i8(self) -> int:
        v = self.stream.read(1)
        return struct.unpack(f"{self._bo}b", v)[0]

    def u8(self) -> int:
        v = self.stream.read(1)
        return struct.unpack(f"{self._bo}B", v)[0]

    def i16(self) -> int:
        v = self.stream.read(2)
        return struct.unpack(f"{self._bo}h", v)[0]

    def u16(self) -> int:
        v = self.stream.read(2)
        return struct.unpack(f"{self._bo}H", v)[0]

    def i32(self) -> int:
        v = self.stream.read(4)
        return struct.unpack(f"{self._bo}i", v)[0]

    def u32(self) -> int:
        v = self.stream.read(4)
        return struct.unpack(f"{self._bo}I", v)[0]

    def i64(self) -> int:
        v = self.stream.read(8)
        return struct.unpack(f"{self._bo}q", v)[0]

    def u64(self) -> int:
        v = self.stream.read(8)
        return struct.unpack(f"{self._bo}Q", v)[0]

    def f32(self) -> float:
        v = self.stream.read(4)
        return struct.unpack(f"{self._bo}f", v)[0]

    def f64(self) -> float:
        v = self.stream.read(8)
        return struct.unpack(f"{self._bo}d", v)[0]

    def cstr(self, encoding: str | None = None) -> str:
        data = bytearray()
        while True:
            b = self.byte()
            if b == 0:
                break
            data.append(b)
        return bytes(data).decode(encoding or self.encoding)

    def pstr(self, encoding: str | None = None, strip: bool = True) -> str:
        l = self.u32()
        data = self.stream.read(l)
        if strip:
            data.rstrip(b"\x00")
        return data.decode(encoding or self.encoding)

    def string(self, size: int, encoding: str | None = None, strip: bool = True) -> str:
        data = self.stream.read(size)
        if strip:
            data.rstrip(b"\x00")
        return data.decode(encoding or self.encoding)
