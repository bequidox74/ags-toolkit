import dataclasses
import io
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal

from _internal.byte_reader import ByteReader
from _internal.string_writer import StringWriter
from _internal.utils import check

type ClibFileType = Literal["ags", "exe", "001", ""]

AGS_SUFFIX = ".ags"
EXE_SUFFIX = ".exe"
OO1_SUFFIX = ".001"

_SUFFIX_TO_TYPE: dict[str, ClibFileType] = {
    AGS_SUFFIX: "ags",
    EXE_SUFFIX: "exe",
    OO1_SUFFIX: "001",
}


@dataclass
class CLib:
    @dataclass
    class File:
        name: str  # cstr
        df_index: int  # u8
        offset: int  # u64
        size: int  # u64

        def __str__(self) -> str:
            return (
                f"{self.name} [{self.df_index}], {self.size} bytes @0x{self.offset:X}"
            )

    START_SIGN: ClassVar[bytes] = b"CLIB\x1a"
    END_SIGN: ClassVar[bytes] = b"CLIB\x01\x02\x03\x04SIGE"

    self_offset: int

    version: int  # u8
    df_index: int  # u8
    num_dfiles: int  # u32
    dfile_names: list[str]  # cstr
    num_files: int  # u32
    files: list[CLib.File]

    @classmethod
    def read(cls, br: ByteReader) -> CLib:
        self_offset = br.tell()
        sig = br.read(len(CLib.START_SIGN))
        check(sig == CLib.START_SIGN, "CLIB start signature mismatch")

        version = br.u8()
        df_index = br.u8()
        check(df_index == 0, "CLIB data file index must be 0")
        br.skip(4)  # reserved options

        num_dfiles = br.u32()
        dfile_names: list[str] = []
        for _ in range(num_dfiles):
            dfile_names.append(br.cstr())

        num_files = br.u32()
        files: list[CLib.File] = []
        for _ in range(num_files):
            name = br.cstr()
            idx = br.u8()
            offset = br.u64()
            size = br.u64()
            files.append(CLib.File(name, idx, offset, size))

        return CLib(
            self_offset,
            version,
            df_index,
            num_dfiles,
            dfile_names,
            num_files,
            files,
        )

    @classmethod
    def read_file(cls, data_path: Path, type_: ClibFileType = "") -> CLib:
        if not type_:
            # determine what we're dealing with.
            suffix = data_path.suffix.casefold()
            type_ = _SUFFIX_TO_TYPE[suffix]

        clib: CLib
        if type_ == "ags":
            clib = CLib.read_ags(data_path)
        elif type_ == "exe":
            clib = CLib.read_exe(data_path)
        elif type_ == "001":
            raise NotImplementedError(".001 is not supported")
        else:
            raise ValueError(f"unknown type: {type_}")
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

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def __str__(self) -> str:
        sw = StringWriter()
        sw.println(f"=== CLIB version {self.version} ===")
        sw.println(f"Version: {self.version}")
        sw.println(f"Number of data files: {self.num_dfiles}")

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
