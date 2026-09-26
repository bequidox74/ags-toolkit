import fnmatch
import io
import os
from pathlib import Path
from typing import Literal

from _internal.byte_reader import ByteReader
from _internal.utils import check, chunked_copy
from game_data import CLib

type ClibFileType = Literal["ags", "exe", "001", ""]

AGS_SUFFIX = ".ags"
EXE_SUFFIX = ".exe"
OO1_SUFFIX = ".001"

_SUFFIX_TO_TYPE: dict[str, ClibFileType] = {
    AGS_SUFFIX: "ags",
    EXE_SUFFIX: "exe",
    OO1_SUFFIX: "001",
}


def read_clib(data_path: Path, type_: ClibFileType = "") -> CLib:
    if not type_:
        # determine what we're dealing with.
        suffix = data_path.suffix.casefold()
        type_ = _SUFFIX_TO_TYPE[suffix]

    clib: CLib
    if type_ == "ags":
        clib = read_ags(data_path)
    elif type_ == "exe":
        clib = read_exe(data_path)
    elif type_ == "001":
        raise NotImplementedError(".001 is not supported")
    else:
        raise ValueError(f"unknown type: {type_}")
    return clib


def read_ags(path: Path) -> CLib:
    with open(path, "rb") as s:
        return CLib.read(ByteReader(s))


def read_exe(path: Path) -> CLib:
    with open(path, "rb") as s:
        br = ByteReader(s)
        s.seek(-(len(CLib.END_SIGN) + 8), io.SEEK_END)
        offset = br.u64()
        signature = s.read(len(CLib.END_SIGN))
        check(signature == CLib.END_SIGN, "CLIB end signature mismatch")

        s.seek(offset)
        return CLib.read(br)


def unpack_assets(dfile: Path, outdir: Path, filter_: str) -> None:
    clib = read_clib(dfile)
    with open(dfile, "rb") as sin:
        br = ByteReader(sin)
        for f in clib.files:
            if not fnmatch.fnmatch(f.name, filter_):
                continue
            br.seek(f.offset)
            outpath = outdir / f.name
            os.makedirs(outdir, exist_ok=True)
            with open(outpath, "wb") as sout:
                chunked_copy(sin, sout, f.size)
