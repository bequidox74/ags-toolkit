from pathlib import Path
from typing import BinaryIO


def check(cond: bool, message: str | None = None) -> None:
    if not cond:
        raise AssertionError(message)


def is_exe(p: Path) -> bool:
    return p.suffix.casefold() == ".exe"


def is_ags(p: Path) -> bool:
    return p.suffix.casefold() == ".ags"


def chunked_copy(
    src: BinaryIO,
    dst: BinaryIO,
    offset: int,
    size: int,
    chunk_size: int = 64 * 1024,
) -> None:
    src.seek(offset)
    copied: int = 0
    while copied < size:
        left = size - copied
        chunk = src.read(min(chunk_size, left))
        dst.write(chunk)
        copied += len(chunk)


def strip_lines(s: str) -> str:
    lines = []
    for line in s.splitlines():
        lines.append(line.rstrip())
    return "\n".join(lines).strip() + "\n"
