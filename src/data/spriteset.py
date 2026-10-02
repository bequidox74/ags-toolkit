import io
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntEnum, IntFlag
from typing import ClassVar, NamedTuple

from _internal.utils import check
from data import decode
from data.character import ByteReader


@dataclass(repr=False)
class SpriteIndex:
    FILENAME: ClassVar = "sprindex.dat"
    SIGNATURE: ClassVar = "SPRINDEX"

    version: int  # u32
    spr_file_id: int  # u32
    last_slot: int  # u32
    count: int  # u32
    widths: list[int]  # u16[]
    heights: list[int]  # u16[]
    offsets: list[int]  # u16[]

    @staticmethod
    def read(br: ByteReader) -> SpriteIndex:
        signature = br.fstr(len(SpriteIndex.SIGNATURE))
        check(signature == SpriteIndex.SIGNATURE, "sprite index signature mismatch")
        version = br.u32()
        spr_file_id = br.u32()
        last_slot = br.u32()
        count = br.u32()
        widths = [br.u16() for _ in range(count)]
        heights = [br.u16() for _ in range(count)]
        offsets = [br.u64() for _ in range(count)]

        return SpriteIndex(
            version=version,
            spr_file_id=spr_file_id,
            last_slot=last_slot,
            count=count,
            widths=widths,
            heights=heights,
            offsets=offsets,
        )


class StoreFlag(IntFlag):
    NONE = 0
    OPTIMIZE_FOR_SIZE = 1


@dataclass(repr=False)
class Sprite:
    class Palette(Enum):
        UNDEFINED = 0
        RGB888 = 32
        ARGB8888 = 33
        RGB565 = 34

    class Compression(IntEnum):
        NONE = 0
        RLE = 1
        LZW = 2

    class Version(IntEnum):
        UNDEFINED = 0
        UNCOMPRESSED = 4
        COMPRESSED = 5
        LAST32BIT = 6
        V64BIT = 10
        HIGHSPRITELIMIT = 11
        STORAGEFORMATS = 12

    bytes_per_pixel: int  # u8
    palette_fmt: Sprite.Palette  # u8
    palette: list[int]  # [u8]
    compression: Compression  # u8
    width: int  # u16
    height: int  # u16
    len_data: int  # u32
    off_data: int  # u8[len_data]

    @staticmethod
    def read_slot(
        version: int,
        def_compr: Sprite.Compression,
        br: ByteReader,
    ) -> Sprite | None:
        start = br.tell()
        bytes_per_pixel = br.u8()
        storage_fmt = Sprite.Palette(br.u8())  # pylint: disable=all
        if bytes_per_pixel == 0:
            return None  # skip empty slots
        assert bytes_per_pixel in (1, 2, 4), "BPP must be 1/2/4"

        num_palette = 0
        compression = def_compr
        if version >= Sprite.Version.STORAGEFORMATS:
            num_palette = br.u8() + 1
            compression = Sprite.Compression(br.u8())
        width = br.u16()
        height = br.u16()

        palette: list[int] = []
        if storage_fmt is not Sprite.Palette.UNDEFINED:
            spec = SPECS[storage_fmt]
            decoder = DECODERS[SPECS[storage_fmt].bpp]
            for _ in range(num_palette):
                palette.append(decoder(br.read(spec.bpp)))

        if (
            version >= Sprite.Version.STORAGEFORMATS
            or compression is not Sprite.Compression.NONE
        ):
            len_data = br.u32()
        else:
            len_data = width * height * bytes_per_pixel
        off_data = br.tell() - start
        br.skip(len_data)

        return Sprite(
            bytes_per_pixel=bytes_per_pixel,
            palette_fmt=storage_fmt,
            palette=palette,
            compression=compression,
            width=width,
            height=height,
            len_data=len_data,
            off_data=off_data,
        )

    def read_bitmap(self, br: ByteReader) -> bytes:
        """Decode sprite data into a RGBA8888 bitmap."""
        raw = br.read(self.len_data)
        decomp: bytes = b""
        size = self.width * self.height * self.bytes_per_pixel

        if self.palette_fmt is not Sprite.Palette.UNDEFINED:
            bpp = 1
        else:
            bpp = self.bytes_per_pixel

        if self.compression == Sprite.Compression.NONE:
            decomp = raw
        elif self.compression == Sprite.Compression.RLE:
            with io.BytesIO(raw) as bio:
                decomp = decode.rle(bpp, size, bio)
        elif self.compression == Sprite.Compression.LZW:
            raise NotImplementedError  # TODO
            # decomp = Sprite.decompress_lzw(raw, br)

        if len(self.palette) > 0:  # indexed
            return self.decode_indexed(decomp)
        else:  # sequential
            return self.decode_sequential(decomp)

    def decode_indexed(self, data: bytes) -> bytes:
        result: list[int] = []
        for i in data:
            result.append(self.palette[i])
        return decode.pack_bitmap(result)

    def decode_sequential(self, data: bytes) -> bytes:
        result: list[int] = []
        bpp = self.bytes_per_pixel
        decoder = DECODERS[bpp]
        with io.BytesIO(data) as sin:
            br = ByteReader(sin)
            while True:
                c = decoder(br.read(bpp))
                if not c:
                    break
                result.append(c)
        return decode.pack_bitmap(result)


type ColorDecoder = Callable[[bytes | memoryview], int]


class FormatSpec(NamedTuple):
    code: Sprite.Palette
    bpp: int


DECODERS: dict[int, ColorDecoder] = {
    2: decode.rgb565,
    3: decode.rgb888,
    4: decode.argb8888,
}

SPECS = {
    spec.code: spec
    for spec in [
        FormatSpec(Sprite.Palette.UNDEFINED, 0),
        FormatSpec(Sprite.Palette.RGB565, 2),
        FormatSpec(Sprite.Palette.RGB888, 3),  # disallowed in 3.6.0.55?
        FormatSpec(Sprite.Palette.ARGB8888, 4),
    ]
}


@dataclass(repr=False)
class SpriteSet:
    FILENAME: ClassVar = "acsprset.spr"
    SIGNATURE: ClassVar = " Sprite File "

    version: int  # u16
    # signature
    compression: Sprite.Compression  # u8
    spr_file_id: int  # u32
    last_slot: int  # u32
    store_flags: int  # u8
    # reserved u8[3]
    off_sprites: int

    @staticmethod
    def read(br: ByteReader) -> SpriteSet:
        begin = br.tell()
        version = br.u16()
        signature = br.fstr(len(SpriteSet.SIGNATURE))
        check(signature == SpriteSet.SIGNATURE, "sprite set signature mismatch")
        compression = Sprite.Compression(br.u8())
        spr_file_id = br.u32()
        last_slot = br.u32()
        store_flags = br.u8()
        br.skip(3)  # reserved
        off_sprites = br.tell() - begin

        return SpriteSet(
            version=version,
            compression=compression,
            spr_file_id=spr_file_id,
            last_slot=last_slot,
            store_flags=store_flags,
            off_sprites=off_sprites,
        )
