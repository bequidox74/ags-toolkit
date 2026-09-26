import argparse
import fnmatch
import os
from io import StringIO
from pathlib import Path

import extract
from _internal.utils import chunked_copy

DEFAULT_CHUNK_SIZE = 64


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    _init_assets_parser(subparsers)

    args = parser.parse_args()
    args.func(args)


def _init_assets_parser(subparsers) -> None:
    assets_parser = subparsers.add_parser("assets")
    assets_parser.add_argument("input", type=Path)
    assets_sub = assets_parser.add_subparsers()

    assets_list = assets_sub.add_parser("list")
    assets_list.add_argument("-q", "--quiet", action="store_true")
    assets_list.add_argument("-o", "--output", type=Path, required=False)
    assets_list.set_defaults(func=list_assets)

    assets_extract = assets_sub.add_parser("extract")
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


def list_assets(args: argparse.Namespace) -> None:
    if args.quiet and args.output is None:
        raise ValueError("--quiet specified with no --output path")
    clib = extract.read_clib(args.input)
    with StringIO() as sio:
        print(str(clib), end="", file=sio, flush=True)
        if not args.quiet:
            print(sio.getvalue())
        if args.output is not None:
            os.makedirs(args.output.parent, exist_ok=True)
            with open(args.output / "assets.index", "w", encoding="utf-8") as f:
                f.write(sio.getvalue())


def extract_assets(args: argparse.Namespace) -> None:
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
            sin.seek(file.offset)
            chunked_copy(sin, sout, file.size, args.chunk_size * 1024)
            extracted += 1
            if not args.quiet:
                print(f"Extracted {file.name}")

    if not args.quiet:
        print(f"Done, {extracted} files in total")


if __name__ == "__main__":
    main()
