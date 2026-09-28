from dataclasses import dataclass
from enum import IntFlag

from extract import ByteReader


class DialogFlag(IntFlag):
    ON = 1 << 0
    OFF_PERM = 1 << 1
    NOREPEAT = 1 << 3
    HAS_BEEN_CHOSEN = 1 << 4


@dataclass
class Dialog:
    options: list[str]  # str[150] * 30
    flags: list[int]  # u32[30]
    option_scripts: int  # u32
    entry_points: list[int]  # u2[30]
    startup_entry_point: int  # u16
    code_size: int  # u16
    num_options: int  # u32
    show_text_parser: bool  # u32

    @classmethod
    def read(cls, br: ByteReader) -> Dialog:
        options = [br.fstr(150) for _ in range(30)]
        flags = [br.u32() for _ in range(30)]
        option_scripts = br.u32()
        entry_points = [br.u16() for _ in range(30)]
        startup_entry_point = br.u16()
        code_size = br.u16()
        num_options = br.u32()
        show_text_parser = bool(br.u32())

        return Dialog(
            options,
            flags,
            option_scripts,
            entry_points,
            startup_entry_point,
            code_size,
            num_options,
            show_text_parser,
        )
