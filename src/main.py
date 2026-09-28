import fnmatch
import json
import os
from argparse import ArgumentParser, Namespace
from io import StringIO
from pathlib import Path

import extract
from _internal.byte_reader import ByteReader
from _internal.utils import chunked_copy
from data.clib import CLib, StringWriter
from data.gamefile import GameData

DEFAULT_CHUNK_SIZE = 64
GAMEDATA_NAME = "game28.dta"


def main() -> None:
    parser = ArgumentParser()
    sub = parser.add_subparsers()
    _init_assets_parser(sub)
    _init_gamedata_parser(sub)

    args = parser.parse_args()
    args.func(args)


def _init_assets_parser(subparsers) -> None:
    assets_parser = subparsers.add_parser("assets")
    assets_parser.add_argument("input", type=Path)
    sub = assets_parser.add_subparsers()

    assets_list = sub.add_parser("list")
    assets_list.add_argument("-q", "--quiet", action="store_true")
    assets_list.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Format index as JSON instead",
    )
    assets_list.add_argument("-o", "--output", type=Path, required=False)
    assets_list.set_defaults(func=list_assets)

    assets_extract = sub.add_parser("extract")
    assets_extract.add_argument("-q", "--quiet", action="store_true")
    assets_extract.add_argument("-o", "--output", type=Path, required=True)
    assets_extract.add_argument(
        "-c",
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Chunk size in kilobytes for copying",
    )
    filter_group = assets_extract.add_mutually_exclusive_group()
    filter_group.add_argument("-i", "--include", type=str)
    filter_group.add_argument("-e", "--exclude", type=str)
    assets_extract.set_defaults(func=extract_assets)


def _init_gamedata_parser(subparsers) -> None:
    gd_parser: ArgumentParser = subparsers.add_parser("gamedata")
    gd_parser.add_argument("input", type=Path)
    gd_parser.add_argument("-j", "--json", action="store_true")
    gd_parser.add_argument("-o", "--output", type=Path, required=True)
    gd_parser.set_defaults(func=extract_gamedata)


def list_assets(args: Namespace) -> None:
    if args.quiet and args.output is None:
        raise ValueError("--quiet specified with no --output path")
    clib = extract.read_clib(args.input)

    with StringIO() as sio:
        if args.json:
            print(json.dumps(clib.to_dict(), indent=2), file=sio)
        else:
            print(str(clib), end="", file=sio)

        if not args.quiet:
            print(sio.getvalue())

        if args.output is not None:
            suffix = ".json" if args.json else ".index"
            outpath = _prepare_output(args.output, f"assets{suffix}")
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(sio.getvalue())


def extract_assets(args: Namespace) -> None:
    clib = extract.read_clib(args.input)
    extracted = 0
    for file in clib.files:
        if file.df_index != 0:
            raise NotImplementedError("multiple data files not supported")

        skip = False
        if args.include is not None:
            filters = args.include.split(",")
            skip = not any(fnmatch.fnmatch(file.name, f) for f in filters)
        elif args.exclude is not None:
            filters = args.exclude.split(",")
            skip = any(fnmatch.fnmatch(file.name, f) for f in filters)
        if skip:
            continue

        outpath = args.output / file.name
        with open(args.input, "rb") as sin, open(outpath, "wb") as sout:
            sin.seek(clib.self_offset + file.offset)
            chunked_copy(sin, sout, file.size, args.chunk_size * 1024)
            extracted += 1
            if not args.quiet:
                print(f"Extracted {file.name}")

    if not args.quiet:
        print(f"Done, {extracted} files in total")


def extract_gamedata(args: Namespace) -> None:
    clib = extract.read_clib(args.input)
    gdata_file: CLib.File
    for file in clib.files:
        if file.name == GAMEDATA_NAME:
            gdata_file = file
            break
    else:
        raise RuntimeError("game28.dta not found in assets")

    with open(args.input, "rb") as sin:
        sin.seek(clib.self_offset + gdata_file.offset)
        gdata = GameData.read(ByteReader(sin))
    outpath = _prepare_output(args.output, "gamedata.json")
    with open(outpath, "w", encoding="utf-8") as sout:
        if args.json:
            json.dump(gdata.to_dict(), sout, indent=2)
        else:
            sw = StringWriter()
            sout.write(gdata.to_index(sw))


def _prepare_output(path: Path, default_name: str) -> Path:
    out: Path
    if path.is_dir():
        out = path / default_name
    else:
        out = path
        os.makedirs(out.parent, exist_ok=True)
    return out


if __name__ == "__main__":
    main()
