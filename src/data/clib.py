import dataclasses
from dataclasses import dataclass
from typing import ClassVar

from _internal.byte_reader import ByteReader
from _internal.string_writer import StringWriter
from _internal.utils import check


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
