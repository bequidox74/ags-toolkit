import dataclasses
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import ClassVar, NamedTuple

from _internal.byte_reader import ByteReader
from _internal.utils import check
from data import encrypt
from data.character import Character
from data.common import Color
from data.dialog import Dialog
from data.view import View

SCOM_SIGNATURE = b"SCOM"
SCOM_END_SIGNATURE = 0xBEEFCAFE


class PaletteType(IntEnum):
    GAMEWIDE = 0
    BACKGROUND = 2


class GameResolutionType(IntEnum):
    UNDEFINED = -1
    DEFAULT = 0
    R320X200 = 1
    R320X240 = 2
    R640X400 = 3
    R640X480 = 4
    R800X600 = 5
    R1024X768 = 6
    R1280X720 = 7
    CUSTOM = 8


@dataclass
class GameSetup:
    @dataclass
    class Resolution:
        width: int  # u32
        height: int  # u32

    NUM_OPTIONS: ClassVar = 100
    NUM_PALETTE_COLORS: ClassVar = 256
    NUM_GAME_MESSAGES: ClassVar = 500

    game_name: str  # 50
    # padding 2
    options: list[int]  # u32[100]
    palette_types: list[PaletteType]  # u1[256]
    palette_colors: list[Color]  # 256
    num_views: int  # u32
    num_chars: int  # u32
    player_char_id: int  # u32
    max_score: int  # u32
    num_inv_items: int  # u16 (= raw - 1)
    # padding 2
    num_dialogs: int  # u32
    num_dlgmessage: int  # u32
    num_fonts: int  # u32
    color_depth: int  # u32
    target_win: int  # u32
    dialog_options_bullet: int  # u32
    hotdot_color: int  # u16
    hotdot_outer_color: int  # u16
    game_unique_id: int  # u32
    num_guis: int  # u32
    num_cursors: int  # u32
    game_resolution_type: GameResolutionType  # u32
    game_resolution: GameSetup.Resolution | None
    lipsync_default_frame: int  # u32
    inv_hotspot_marker_image: int  # u32
    # reserved 17 * 4
    has_game_message: list[bool]  # 500
    load_dictionary: bool  # u32
    global_scr_not_null: bool  # u32
    chars_not_null: bool  # u32
    compiled_scr_not_null: bool  # u32

    @classmethod
    def read(cls, br: ByteReader) -> GameSetup:
        game_name = br.string(50)
        br.skip(2)
        options: list[int] = []
        for _ in range(GameSetup.NUM_OPTIONS):
            options.append(br.u32())
        palette_types: list[PaletteType] = []
        for _ in range(GameSetup.NUM_PALETTE_COLORS):
            palette_types.append(PaletteType(br.u8()))
        palette_colors: list[Color] = []
        for _ in range(GameSetup.NUM_PALETTE_COLORS):
            r = br.u8() * 4
            g = br.u8() * 4
            b = br.u8() * 4
            br.skip(1)
            palette_colors.append(Color(r, g, b))
        num_views = br.u32()
        num_chars = br.u32()
        player_char_id = br.u32()
        max_score = br.u32()
        num_inv_items = br.u16() - 1
        br.skip(2)
        num_dialogs = br.u32()
        num_dlgmessage = br.u32()
        num_fonts = br.u32()
        color_depth = br.u32()
        target_win = br.u32()
        dialog_options_bullet = br.u32()
        hotdot_color = br.u16()
        hotdot_outer_color = br.u16()
        game_unique_id = br.u32()
        num_guis = br.u32()
        num_cursors = br.u32()
        game_resolution_type = GameResolutionType(br.u32())
        game_resolution: GameSetup.Resolution | None = None
        if game_resolution_type is GameResolutionType.CUSTOM:
            w = br.u32()
            h = br.u32()
            game_resolution = GameSetup.Resolution(w, h)
        lipsync_default_frame = br.u32()
        inv_hotspot_marker_image = br.u32()
        br.skip(17 * 4)
        has_game_message: list[bool] = []
        for _ in range(GameSetup.NUM_GAME_MESSAGES):
            has_game_message.append(bool(br.u32()))
        load_dictionary = bool(br.u32())
        global_scr_not_null = bool(br.u32())
        chars_not_null = bool(br.u32())
        compiled_scr_not_null = bool(br.u32())

        return GameSetup(
            game_name,
            options,
            palette_types,
            palette_colors,
            num_views,
            num_chars,
            player_char_id,
            max_score,
            num_inv_items,
            num_dialogs,
            num_dlgmessage,
            num_fonts,
            color_depth,
            target_win,
            dialog_options_bullet,
            hotdot_color,
            hotdot_outer_color,
            game_unique_id,
            num_guis,
            num_cursors,
            game_resolution_type,
            game_resolution,
            lipsync_default_frame,
            inv_hotspot_marker_image,
            has_game_message,
            load_dictionary,
            global_scr_not_null,
            chars_not_null,
            compiled_scr_not_null,
        )


@dataclass
class Font:
    flags: int  # u32
    size_multiplier: int  # i32
    outline: int  # i32
    vertical_offset: int  # i32
    line_spacing: int  # i32

    @classmethod
    def read(cls, br: ByteReader) -> Font:
        flags = br.u32()
        size_multiplier = br.i32()
        outline = br.i32()
        vertical_offset = br.i32()
        line_spacing = br.i32()
        return Font(
            flags,
            size_multiplier,
            outline,
            vertical_offset,
            line_spacing,
        )


class SpriteFlags(IntFlag):
    HIRES = 1 << 0
    HICOLOR = 1 << 1
    DYNAMIC_ALLOC = 1 << 2
    TRUE_COLOR = 1 << 3
    ALPHA_CHANNEL = 1 << 4
    VAR_RESOLUTION = 1 << 5


@dataclass
class InventoryItem:
    description: str  # 25
    # padding 3
    image: int  # u32
    cursor_image: int  # u32
    hotspot_x: int  # i32
    hotspot_y: int  # i32
    # reserved 5 * 4
    player_starts_with: bool  # u8
    # padding 3

    @classmethod
    def read(cls, br: ByteReader) -> InventoryItem:
        description = br.string(25)
        br.skip(3)
        image = br.u32()
        cursor_image = br.u32()
        hotspot_x = br.i32()
        hotspot_y = br.i32()
        br.skip(5 * 4)
        player_starts_with = bool(br.u8())
        br.skip(3)

        return InventoryItem(
            description,
            image,
            cursor_image,
            hotspot_x,
            hotspot_y,
            player_starts_with,
        )


@dataclass
class Cursor:
    image: int  # u32
    hotspot_x: int  # i16
    hotspot_y: int  # i16
    num_views: int  # u16
    name: str  # 10
    flags: int  # u8
    # padding 3

    @classmethod
    def read(cls, br: ByteReader) -> Cursor:
        image = br.u32()
        hotspot_x = br.i16()
        hotspot_y = br.i16()
        num_views = br.u16()
        name = br.string(10)
        flags = br.u8()
        br.skip(3)

        return Cursor(
            image,
            hotspot_x,
            hotspot_y,
            num_views,
            name,
            flags,
        )


@dataclass
class InteractionScript:
    num_scripts: int  # u32
    sciprt_names: list[str]  # cstr

    @classmethod
    def read(cls, br: ByteReader) -> InteractionScript:
        num_scripts = br.u32()
        names: list[str] = []
        for _ in range(num_scripts):
            names.append(br.cstr())
        return InteractionScript(num_scripts, names)


@dataclass
class ParserWord:
    word: str
    word_group: int  # u16

    @classmethod
    def read(cls, br: ByteReader) -> ParserWord:
        size = br.u32()
        encrypted = br.read(size)
        word = encrypt.decrypt(encrypted)
        word_group = br.u16()
        return ParserWord(word, word_group)


class Script(NamedTuple):
    offset: int
    size: int
    name: str


@dataclass
class GameData:
    SIGNATURE: ClassVar = "Adventure Creator Game File v2"

    version: int  # u32
    len_editor_version: int  # u32
    editor_version: str  # str[len_editor_version]
    extended_engine_caps: int
    game_setup: GameSetup
    guid: str  # str[40]
    save_game_file_ext: str  # str[20]
    save_game_folder_name: str  # str[50]
    fonts: list[Font]
    topmost_sprite: int  # u32
    sprite_flags: list[int]
    inventory_items: list[InventoryItem]
    cursors: list[Cursor]
    char_interact_scripts: list[InteractionScript]
    inv_item_interact_scripts: list[InteractionScript]
    # num_parser_words: int  # u32
    parser_words: list[ParserWord]
    global_script: Script
    dialog_script: Script
    # num_scripts: int  # u32
    scripts: list[Script]
    views: list[View]
    characters: list[Character]
    lipsync: list[str]
    dialogs: list[Dialog]

    @classmethod
    def read(cls, br: ByteReader) -> GameData:
        signature = br.string(len(GameData.SIGNATURE))
        check(signature == GameData.SIGNATURE, "game data file signature mismatch")
        version = br.u32()
        len_editor_version = br.u32()
        editor_version = br.string(len_editor_version)
        extended_engine_caps = br.u32()
        game_setup = GameSetup.read(br)
        guid = br.string(40)
        save_game_file_ext = br.string(20)
        save_game_folder_name = br.string(50)
        fonts: list[Font] = []
        for _ in range(game_setup.num_fonts):
            fonts.append(Font.read(br))
        topmost_sprite = br.u32() - 1
        sprite_flags: list[int] = []
        for _ in range(topmost_sprite + 1):
            sprite_flags.append(br.u8())
        br.skip(68)  # unused inventory item slot 0
        inventory_items: list[InventoryItem] = []
        for _ in range(game_setup.num_inv_items):
            inventory_items.append(InventoryItem.read(br))
        cursors: list[Cursor] = []
        for _ in range(game_setup.num_cursors):
            cursors.append(Cursor.read(br))
        char_interact_scripts: list[InteractionScript] = []
        for _ in range(game_setup.num_chars):
            char_interact_scripts.append(InteractionScript.read(br))
        inv_item_interact_scripts: list[InteractionScript] = []
        for _ in range(game_setup.num_inv_items):
            inv_item_interact_scripts.append(InteractionScript.read(br))
        num_parser_words = br.u32()
        parser_words: list[ParserWord] = []
        for _ in range(num_parser_words):
            parser_words.append(ParserWord.read(br))
        global_script = skip_scom(br)
        dialog_script = skip_scom(br)
        num_scripts = br.u32()
        scripts: list[Script] = [skip_scom(br) for _ in range(num_scripts)]
        views: list[View] = [View.read(br) for _ in range(game_setup.num_views)]
        characters: list[Character] = [
            Character.read(br) for _ in range(game_setup.num_chars)
        ]
        lipsync = [br.string(50) for _ in range(20)]
        global_messages: list[str] = []
        while True:
            size = br.u32()
            if size == 0:
                break
            global_messages.append(encrypt.decrypt(br.read(size)))
        dialogs = [Dialog.read(br) for _ in range(game_setup.num_dialogs)]

        return GameData(
            version,
            len_editor_version,
            editor_version,
            extended_engine_caps,
            game_setup,
            guid,
            save_game_file_ext,
            save_game_folder_name,
            fonts,
            topmost_sprite,
            sprite_flags,
            inventory_items,
            cursors,
            char_interact_scripts,
            inv_item_interact_scripts,
            parser_words,
            global_script,
            dialog_script,
            scripts,
            views,
            characters,
            lipsync,
            dialogs,
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def skip_scom(br: ByteReader) -> Script:
    offset = br.tell()
    br.skip(len(SCOM_SIGNATURE) + 4)
    len_gdata = br.u32()
    num_codes = br.u32()
    len_strings = br.u32()
    br.skip(len_gdata)
    br.skip(num_codes * 4)
    br.skip(len_strings)
    num_fixups = br.u32()
    br.skip(num_fixups)  # fixup types
    br.skip(num_fixups * 4)  # fixups
    num_imports = br.u32()
    for _ in range(num_imports):
        br.cstr()  # name
    num_exports = br.u32()
    for _ in range(num_exports):
        br.cstr()  # name
        br.skip(4)  # address
    num_sections = br.u32()
    section_names: list[str] = []
    for _ in range(num_sections):
        section_names.append(br.cstr())  # name
        br.skip(4)  # offset
    br.skip(4)  # signature
    size = br.tell() - offset

    name = section_names[0] if section_names else ""
    return Script(offset, size, name)
