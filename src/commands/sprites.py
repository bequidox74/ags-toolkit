import logging
from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from pathlib import Path
from typing import NamedTuple

from PIL import Image

from _internal import utils
from _internal.byte_reader import ByteReader
from _internal.utils import check
from data.clib import CLib
from data.spriteset import Sprite, SpriteIndex, SpriteSet

logger = logging.getLogger(__name__)


class _Files(NamedTuple):
    sprset: tuple[SpriteSet, int, Path]
    spridx: SpriteIndex | None


ACSPRSET_FILE = "acsprset.spr"
SPRINDEX_FILE = "sprindex.dat"


def init_parser(subp) -> None:
    parser: ArgumentParser = subp.add_parser(
        "sprites",
        help="extract sprites",
    )
    parser.add_argument(
        "input",
        type=Path,
        help=f"input file (.exe/.ags/{ACSPRSET_FILE}/{SPRINDEX_FILE})",
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
        "--index",
        action=BooleanOptionalAction,
        default=None,
        help="use a sprite index file to speed up operation",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="png",
        help="file format to use for saving",
    )
    parser.add_argument(
        "-r",
        "--ranges",
        help="comma-separated list of ranges to extract (1,2-5,7)",
        default="",
    )
    parser.set_defaults(func=_extract)


def _extract(args: Namespace) -> None:
    extract(args.input, args.output, args.dry_run, args.ranges, args.index, args.format)


def extract(
    pin: Path,
    pout: Path,
    dry_run: bool,
    ranges_str: str,
    use_index: bool | None,
    file_format: str,
) -> None:
    ranges = _process_ranges(ranges_str)
    files = _read_files(pin)
    if not ranges:
        ranges = [range(files.sprset[0].last_slot + 1)]

    if use_index is not None:
        if use_index and files.spridx is None:
            raise ValueError("sprite index is required but could not be located")
    else:
        use_index = files.spridx is not None

    if use_index:
        # look up files in the index
        _process_index(pout, files, ranges, dry_run, file_format)
    else:
        # read sprites directly
        _process_noindex(pout, files, ranges, dry_run, file_format)


def _process_index(
    pout: Path,
    files: _Files,
    ranges: list[range],
    dry_run: bool,
    fmt: str,
) -> None:
    spridx = files.spridx
    assert spridx is not None
    sprset, off_sprset, sprset_path = files.sprset
    with open(sprset_path, "rb") as sin:
        br = ByteReader(sin)
        for r in ranges:
            for i in r:
                offset = spridx.offsets[i]
                sin.seek(off_sprset + offset)
                sprite = Sprite.read_slot(sprset.version, sprset.compression, br)
                if sprite is None:
                    continue
                sin.seek(off_sprset + offset + sprite.off_data)
                bitmap = sprite.read_bitmap(br)
                if not dry_run:
                    _save_bitmap(
                        pout / f"{i}.{fmt}", bitmap, sprite.width, sprite.height
                    )
                logger.info("Extracted sprite %d", i)


def _process_noindex(
    pout: Path,
    files: _Files,
    ranges: list[range],
    dry_run: bool,
    fmt: str,
) -> None:
    logger.warning("Reading sprites directly as the index was not located")
    sprset, off_sprset, sprset_path = files.sprset
    with open(sprset_path, "rb") as sin:
        sin.seek(off_sprset + sprset.off_sprites)
        br = ByteReader(sin)
        r_iter = iter(ranges)
        r = next(r_iter)  # guaranteed to exist
        for i in range(sprset.last_slot + 1):
            if i >= r.stop:
                try:
                    r = next(r_iter)
                except StopIteration:
                    break
            offset = br.tell()
            sprite = Sprite.read_slot(sprset.version, sprset.compression, br)
            if i not in r or sprite is None:
                continue
            sin.seek(offset + sprite.off_data)
            bitmap = sprite.read_bitmap(br)
            if not dry_run:
                _save_bitmap(pout / f"s{i}.{fmt}", bitmap, sprite.width, sprite.height)
            logger.info("Extracted sprite %d", i)


def _process_ranges(ranges_str: str) -> list[range]:
    ranges: list[range] = []
    if ranges_str:
        try:
            ranges = _parse_ranges(ranges_str)
        except ValueError:
            logger.exception("Error while parsing range spec:")
            raise
    return ranges


def _read_files(pin: Path) -> _Files:
    if pin.name == ACSPRSET_FILE:
        files = _read_sprset(pin)
    elif pin.name == SPRINDEX_FILE:
        files = _read_spridx(pin)
    elif utils.is_exe(pin) or utils.is_ags(pin):
        files = _read_clib(pin)
    else:
        raise ValueError(f"unknown input file format: {pin.suffix}")
    return files


def _read_sprset(pin: Path) -> _Files:
    spridx = None
    with open(pin, "rb") as sin:
        sprset = SpriteSet.read(ByteReader(sin))
        # check for sibling index
        spridx_path = pin.parent / SPRINDEX_FILE
        if spridx_path.exists():
            with open(spridx_path, "rb") as sin:
                spridx = SpriteIndex.read(ByteReader(sin))
            spridx = _validate_id(sprset, spridx)
        else:
            logger.info(
                "No sibling %s found; will read sprites directly", SPRINDEX_FILE
            )
    return _Files((sprset, 0, pin), spridx)


def _read_spridx(pin: Path) -> _Files:
    # check for the spriteset first
    sprset_path = pin.parent / ACSPRSET_FILE
    check(sprset_path.exists(), f"{ACSPRSET_FILE} must be a sibling of the input file")
    spridx = None
    with open(pin, "rb") as spridx_sin, open(sprset_path, "rb") as sprset_sin:
        spridx = SpriteIndex.read(ByteReader(spridx_sin))
        sprset = SpriteSet.read(ByteReader(sprset_sin))
        spridx = _validate_id(sprset, spridx)
    return _Files((sprset, 0, sprset_path), spridx)


def _read_clib(pin: Path) -> _Files:
    clib = CLib.read_file(pin)
    sprset_file = clib[ACSPRSET_FILE]
    spridx = None
    with open(pin, "rb") as clib_sin:
        off_sprset = clib.self_offset + sprset_file.offset
        clib_sin.seek(off_sprset)
        sprset = SpriteSet.read(ByteReader(clib_sin))
        try:
            spridx_file = clib[SPRINDEX_FILE]
        except KeyError:
            logger.warning(
                "No %s found in CLIB %s; will read sprites directly",
                SPRINDEX_FILE,
                pin.name,
            )
        else:
            off_spridx = clib.self_offset + spridx_file.offset
            clib_sin.seek(off_spridx)
            spridx = SpriteIndex.read(ByteReader(clib_sin))
            spridx = _validate_id(sprset, spridx)
    return _Files((sprset, off_sprset, pin), spridx)


def _validate_id(sprset: SpriteSet, spridx: SpriteIndex) -> SpriteIndex | None:
    result = spridx
    if sprset.spr_file_id != result.spr_file_id:
        result = None
        logger.warning(
            "Sprite index ID mismatch! Falling back to reading sprites directly."
        )
    return result


def _parse_ranges(s: str) -> list[range]:
    result: list[range] = []
    parts = s.split(",")
    check(len(parts) > 0, "attempt to parse empty range spec")

    # collect
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
            raise ValueError("range spec item must be of form 'n' or 'm-n'")

    if not result:
        return result

    # sort & merge
    result.sort(key=lambda r: r.start)
    merged: list[range] = [result[0]]
    for r in result[1:]:
        last = merged[-1]
        if r.start < last.stop:
            merged[-1] = range(last.start, max(last.stop, r.stop))
        else:
            merged.append(r)

    return merged


def _save_bitmap(pout: Path, bm: bytes, w: int, h: int):
    image = Image.frombytes("RGBA", (w, h), bm)
    image.save(pout)
