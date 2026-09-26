import argparse
from pathlib import Path

import extract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    extract.read_clib(args.input)


if __name__ == "__main__":
    main()
