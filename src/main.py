import logging
from argparse import ArgumentParser

from commands import sprites, unpack


def main() -> None:
    parser = ArgumentParser(
        prog="AGS Toolkit",
        description="Tools for Adventure Game Studio games",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress console output",
    )

    subp = parser.add_subparsers(title="commands")
    unpack.init_parser(subp)
    sprites.init_parser(subp)

    args = parser.parse_args()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logging.root.disabled = args.quiet
    args.func(args)  # pass control to the command


if __name__ == "__main__":
    main()
