import logging
import os
from argparse import ArgumentParser, Namespace
from fnmatch import fnmatch
from pathlib import Path

from _internal import utils
from data.clib import CLib

logger = logging.root

CHUNK_SIZE_KIB = 64


def init_parser(subp) -> None:
    parser: ArgumentParser = subp.add_parser(
        "unpack",
        help="unpack assets contained in an AGS game",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="input file (.exe of .ags)",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="output directory (will be created if needed)",
    )
    parser.add_argument(
        "-c",
        "--chunk-size",
        default=CHUNK_SIZE_KIB,
        type=int,
        help=f"chunk size in KiB for copying (default is {CHUNK_SIZE_KIB})",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="do a dry run without writing any files",
    )

    filters = parser.add_mutually_exclusive_group()
    filters.add_argument(
        "-i",
        "--include",
        nargs="+",
        help="wildcard for included files",
    )
    filters.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        help="wildcard for excluded files",
    )

    parser.set_defaults(func=unpack)


def unpack(args: Namespace) -> None:
    pin: Path = args.input
    pout: Path = args.output
    include: list[str] = args.include
    exclude: list[str] = args.exclude
    chunk_size: int = args.chunk_size
    dry_run: bool = args.dry_run

    clib = CLib.read_file(pin)
    logger.info("Read CLIB listing %d files", len(clib.files))
    count = 0
    for f in clib.files:
        if not _filter(f.name, include, exclude):
            continue

        if not dry_run:
            os.makedirs(pout, exist_ok=True)
            with open(pin, "rb") as sin, open(pout / f.name, "wb") as sout:
                offset = clib.self_offset + f.offset
                utils.chunked_copy(sin, sout, offset, f.size, chunk_size)

        count += 1
        logger.info("Extracted '%s' (%d bytes)", f.name, f.size)
    logger.info("Done, %d assets extracted to %s", count, pin)


def _filter(fname: str, inc: list[str], exc: list[str]) -> bool:
    if inc:
        return any(fnmatch(fname, f) for f in inc)
    elif exc:
        return not any(fnmatch(fname, f) for f in exc)
    else:
        return True
