import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path

from _internal import utils
from _internal.byte_reader import ByteReader
from _internal.utils import check
from data.clib import CLib
from data.spriteset import SpriteSet

logger = logging.getLogger(__name__)

SPRITESET_FILE = "acsprset.spr"
INDEX_FILE = "sprindex.dat"


def init_parser(subp) -> None:
    parser: ArgumentParser = subp.add_parser(
        "sprites",
        help="extract sprites",
    )
    parser.add_argument(
        "input",
        type=Path,
        help=f"input file (.exe/.ags/{SPRITESET_FILE}/{INDEX_FILE})",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="output directory (will be created if needed)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="do a dry run without writing any files",
    )
    parser.add_argument(
        "-r",
        "--ranges",
        help="comma-separated list of ranges to extract (1,2-5,7)",
    )
    parser.set_defaults(func=_extract)


def _extract(args: Namespace) -> None:
    extract(args.input, args.output, args.dry_run, args.ranges)


def extract(pin: Path, pout: Path, dry_run: bool, ranges_str: str | None) -> None:
    ranges: list[range] = []
    if ranges_str:
        ranges = _parse_ranges(ranges_str)

    name = pin.name.casefold()
    clib: CLib | None = None
    if name == SPRITESET_FILE:
        # check for sprite index for a speed-up.
        pass
    elif name == INDEX_FILE:
        # sprite set must be a sibling.
        pass
    elif utils.is_exe(pin):
        # try to extract index, fallback to spriteset on id mismatch.
        clib = CLib.read_exe(pin)
    elif utils.is_ags(pin):
        clib = CLib.read_ags(pin)
    else:
        raise ValueError(f"unknown file type: {pin.suffix}")

    if clib is not None:  # .exe/.ags
        sprset_file = clib["acsprset.spr"]
        with open(pin, "rb") as sin:
            br = ByteReader(sin)

            off_sprset = clib.self_offset + sprset_file.offset
            sin.seek(off_sprset)
            sprset = SpriteSet.read(br)

            if not ranges:
                ranges.append(range(len(sprset.slots)))
            for r in ranges:
                for i in r:
                    slot = sprset.slots[i]
                    if slot is None:
                        continue
                    sin.seek(off_sprset + slot.off_data)
                    bitmap = slot.read(br)
    else:  # acsprset.spr/sprindex.dat
        pass


def _parse_ranges(s: str) -> list[range]:
    result: list[range] = []
    parts = s.split(",")
    check(len(parts) > 0)
    for p in parts:
        check(bool(p))
        bounds = p.split("-")
        if len(bounds) == 1:
            i = int(p)
            result.append(range(i, i + 1))
        elif len(bounds) == 2:
            start, end = int(bounds[0]), int(bounds[1])
            result.append(range(start, end + 1))
        else:
            raise ValueError(f"illegal range spec: {s}")
    return result
