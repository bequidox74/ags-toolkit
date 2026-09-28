import io
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from _internal.byte_reader import ByteReader
from _internal.string_writer import StringWriter
from _internal.utils import check


@dataclass
class File:
    name: str  # cstr
    df_index: int  # u8
    offset: int  # u64
    size: int  # u64

    def __str__(self) -> str:
        return f"{self.name} [{self.df_index}], {self.size} bytes @0x{self.offset:X}"

    @classmethod
    def read(cls, br: ByteReader) -> File:
        return File(
            name=br.cstr(),
            df_index=br.u8(),
            offset=br.u64(),
            size=br.u64(),
        )


@dataclass
class CLib:
    START_SIGN: ClassVar[bytes] = b"CLIB\x1a"
    END_SIGN: ClassVar[bytes] = b"CLIB\x01\x02\x03\x04SIGE"

    self_offset: int

    version: int  # u8
    df_index: int  # u8
    dfile_names: list[str]  # cstr
    files: list[File]

    @classmethod
    def read(cls, br: ByteReader) -> CLib:
        self_offset = br.tell()
        sig = br.read(len(CLib.START_SIGN))
        check(sig == CLib.START_SIGN, "CLIB start signature mismatch")

        version = br.u8()
        df_index = br.u8()
        check(df_index == 0, "CLIB data file index must be 0")
        br.skip(4)  # reserved options
        dfile_names: list[str] = [br.cstr() for _ in range(br.u32())]
        files: list[File] = [File.read(br) for _ in range(br.u32())]

        return CLib(
            self_offset,
            version,
            df_index,
            dfile_names,
            files,
        )

    @classmethod
    def read_file(cls, data_path: Path) -> CLib:
        suffix = data_path.suffix.casefold()
        clib: CLib
        if suffix == ".ags":
            clib = CLib.read_ags(data_path)
        elif suffix == ".exe":
            clib = CLib.read_exe(data_path)
        elif suffix == ".001":
            raise NotImplementedError(".001 is not supported")
        else:
            raise ValueError(f"unknown type: {suffix}")
        return clib

    @classmethod
    def read_ags(cls, path: Path) -> CLib:
        with open(path, "rb") as s:
            return CLib.read(ByteReader(s))

    @classmethod
    def read_exe(cls, path: Path) -> CLib:
        with open(path, "rb") as s:
            br = ByteReader(s)
            s.seek(-(len(CLib.END_SIGN) + 8), io.SEEK_END)
            offset = br.u64()
            signature = s.read(len(CLib.END_SIGN))
            check(signature == CLib.END_SIGN, "CLIB end signature mismatch")

            s.seek(offset)
            return CLib.read(br)

    def __getitem__(self, key: str) -> File:
        for f in self.files:
            if f.name == key:
                return f
        raise KeyError(f"asset not found: {key}")

    def __str__(self, sw: StringWriter | None = None) -> str:
        if sw is None:
            sw = StringWriter()

        sw.println(f"=== CLIB version {self.version} ===")
        sw.println(f"Version: {self.version}")
        sw.println(f"Number of data files: {len(self.dfile_names)}")

        sw.println("Data file names:")
        sw.indent()
        for name in self.dfile_names:
            sw.println(f"- {name}")
        sw.println()
        sw.dedent()

        sw.println("Assets:")
        sw.indent()
        for file in self.files:
            sw.println(f"- {file!s}")
        sw.println()
        sw.dedent()

        return str(sw)
