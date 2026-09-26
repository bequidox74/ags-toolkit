import dataclasses
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

from _internal.byte_reader import ByteReader
from _internal.utils import check
from data.common import Color


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
        num_inv_items = br.u16()
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
class GameData:
    SIGNATURE: ClassVar = "Adventure Creator Game File v2"

    version: int  # u32
    len_editor_version: int  # u32
    editor_version: str  # str[len_editor_version]
    extended_engine_caps: int
    game_setup: GameSetup
    # guid: str  # str[40]
    # save_game_file_ext: str  # str[20]
    # save_game_folder_name: str  # str[50]
    # fonts: list[object]
    # topmost_sprite: int  # u32
    # sprite_flags: list[int]

    @classmethod
    def read(cls, br: ByteReader) -> GameData:
        signature = br.string(len(GameData.SIGNATURE))
        check(signature == GameData.SIGNATURE, "game data file signature mismatch")
        version = br.u32()
        len_editor_version = br.u32()
        editor_version = br.string(len_editor_version)
        extended_engine_caps = br.u32()
        game_setup = GameSetup.read(br)

        return GameData(
            version,
            len_editor_version,
            editor_version,
            extended_engine_caps,
            game_setup,
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
