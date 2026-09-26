import argparse
import os
from io import StringIO
from pathlib import Path

import extract


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    assets_parser = subparsers.add_parser("assets")
    assets_parser.add_argument("input", type=Path)
    assets_sub = assets_parser.add_subparsers()

    assets_list = assets_sub.add_parser("list")
    assets_list.add_argument("-q", "--quiet", type=bool, default=False)
    assets_list.add_argument("-o", "--output", type=Path, required=True)
    assets_list.set_defaults(func=list_assets)

    args = parser.parse_args()
    args.func(args)


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
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(sio.getvalue())


if __name__ == "__main__":
    main()
