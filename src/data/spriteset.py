import io
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntEnum, IntFlag
from typing import ClassVar, Self

from _internal.utils import check
from data.character import ByteReader
from data.common import Color, ColorRGBA


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


type ColorDecoder = Callable[[bytes], ColorRGBA]


@dataclass(repr=False)
class Sprite:
    class StorageFormat(Enum):
        @staticmethod
        def decode_rgb888(b: bytes) -> ColorRGBA:
            c = int.from_bytes(b[:3], byteorder=sys.byteorder)
            return ColorRGBA((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF, 255)

        @staticmethod
        def decode_argb8888(b: bytes) -> ColorRGBA:
            c = int.from_bytes(b[:4], byteorder=sys.byteorder)
            return ColorRGBA(
                (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF, (c >> 24) & 0xFF
            )

        @staticmethod
        def decode_rgb565(b: bytes) -> ColorRGBA:
            c = int.from_bytes(b[:2], byteorder=sys.byteorder)
            return ColorRGBA((c >> 11) & 0x1F, (c >> 5) & 0x2F, c & 0x1F, 255)

        decode: ColorDecoder
        bpp: int

        UNDEFINED = (0, None, 0)  # type: ignore
        PALETTE_RGB888 = (32, decode_rgb888, 3)  # 3 bytes
        PALETTE_ARGB8888 = (33, decode_argb8888, 4)  # 4 bytes
        PALETTE_RGB565 = (34, decode_rgb565, 2)  # 2 bytes

        def __new__(cls, value: int, decoder: ColorDecoder, bpp: int) -> Self:
            obj = object.__new__(cls)
            obj._value_ = value
            obj.decode = decoder
            obj.bpp = bpp
            return obj

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
    storage_fmt: Sprite.StorageFormat  # u8
    palette: list[Color]  # [u8]
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
        bytes_per_pixel = br.u8()
        storage_fmt = Sprite.StorageFormat(br.u8())  # pylint: disable=all
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

        palette: list[Color] = []
        if storage_fmt.bpp > 0:
            for _ in range(num_palette):
                palette.append(storage_fmt.decode(br.read(storage_fmt.bpp)))

        if (
            version >= Sprite.Version.STORAGEFORMATS
            or compression is not Sprite.Compression.NONE
        ):
            len_data = br.u32()
        else:
            len_data = width * height * bytes_per_pixel
        off_data = br.tell()
        br.skip(len_data)

        return Sprite(
            bytes_per_pixel=bytes_per_pixel,
            storage_fmt=storage_fmt,
            palette=palette,
            compression=compression,
            width=width,
            height=height,
            len_data=len_data,
            off_data=off_data,
        )

    def read(self, br: ByteReader) -> bytes:
        """Decode sprite data into a RGBA8888 bitmap."""
        raw = br.read(self.len_data)
        decomp: bytes = b""
        if self.compression == Sprite.Compression.NONE:
            decomp = raw
        elif self.compression == Sprite.Compression.RLE:
            decomp = Sprite.decompress_rle(raw)
        elif self.compression == Sprite.Compression.LZW:
            decomp = Sprite.decompress_lzw(raw)

        if len(self.palette) > 0:  # indexed
            return self.decode_indexed(decomp)
        else:  # sequential
            return self.decode_sequential(decomp)

    @staticmethod
    def decompress_rle(data: bytes) -> bytes:
        raise NotImplementedError  # TODO

    @staticmethod
    def decompress_lzw(data: bytes) -> bytes:
        raise NotImplementedError  # TODO

    def decode_indexed(self, data: bytes) -> bytes:
        result = bytearray()
        for b in data:
            result.extend(self.palette[b].rgba_bytes())
        return bytes(result)

    def decode_sequential(self, data: bytes) -> bytes:
        result = bytearray()
        fmt = self.storage_fmt
        with io.BytesIO(data) as sin:
            br = ByteReader(sin)
            c = fmt.decode(br.read(fmt.bpp))
            result.extend(c.rgba_bytes())
        return bytes(result)


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
