import dataclasses
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import ClassVar, NamedTuple

from _internal.byte_reader import ByteReader
from _internal.string_writer import StringWriter
from _internal.utils import check
from data import encrypt
from data.character import Character
from data.common import Color
from data.dialog import Dialog
from data.gui import GameGuis
from data.view import View

SCOM_SIGNATURE = b"SCOM"
SCOM_END_SIGNATURE = 0xBEEFCAFE


@dataclass
class GameSetup:
    class Resolution(NamedTuple):
        width: int  # u32
        height: int  # u32

        def __str__(self) -> str:
            return f"{self.width}x{self.height}"

    class PaletteType(IntEnum):
        GAMEWIDE = 0
        BACKGROUND = 2

    class ResolutionType(IntEnum):
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

    class Option(IntEnum):
        DEBUGMODE = 0
        SCORESOUND = 1
        WALKONLOOK = 2
        DIALOGIFACE = 3
        ANTIGLIDE = 4
        TWCUSTOM = 5
        DIALOGGAP = 6
        NOSKIPTEXT = 7
        DISABLEOFF = 8
        ALWAYSSPCH = 9
        SPEECHTYPE = 10
        PIXPERFECT = 11
        NOWALKMODE = 12
        LETTERBOX = 13
        FIXEDINVCURSOR = 14
        NOLOSEINV = 15
        HIRES_FONTS = 16
        SPLITRESOURCES = 17
        ROTATECHARS = 18
        FADETYPE = 19
        HANDLEINVCLICKS = 20
        MOUSEWHEEL = 21
        DIALOGNUMBERED = 22
        DIALOGUPWARDS = 23
        CROSSFADEMUSIC = 24
        ANTIALIASFONTS = 25
        THOUGHTGUI = 26
        TURNTOFACELOC = 27
        RIGHTLEFTWRITE = 28
        DUPLICATEINV = 29
        SAVESCREENSHOT = 30
        PORTRAITSIDE = 31
        STRICTSCRIPTING = 32
        LEFTTORIGHTEVAL = 33
        COMPRESSSPRITES = 34
        STRICTSTRINGS = 35
        NEWGUIALPHA = 36
        RUNGAMEDLGOPTS = 37
        NATIVECOORDINATES = 38
        GLOBALTALKANIMSPD = 39
        HIGHESTOPTION_321 = 39
        SPRITEALPHA = 40
        SAFEFILEPATHS = 41
        DIALOGOPTIONSAPI = 42
        BASESCRIPTAPI = 43
        SCRIPTCOMPATLEV = 44
        RENDERATSCREENRES = 45
        RELATIVEASSETRES = 46
        WALKSPEEDABSOLUTE = 47
        CLIPGUICONTROLS = 48
        GAMETEXTENCODING = 49
        KEYHANDLEAPI = 50
        CUSTOMENGINETAG = 51
        NOMODMUSIC = 98
        LIPSYNCTEXT = 99

    class SpriteFlag(IntFlag):
        HIRES = 1
        HICOLOR = 2
        DYNAMICALLOC = 4
        TRUECOLOR = 8
        ALPHACHANNEL = 16
        VAR_RESOLUTION = 32
        HADALPHACHANNEL = 64

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
    num_invitems: int  # u16 (= raw - 1)
    # padding 2
    num_dialogs: int  # u32
    num_dlgmessage: int  # u32
    num_fonts: int  # u32
    color_depth: int  # u32
    target_win: int  # u32
    dialog_options_bullet: int  # u32
    hotdot_color: int  # u16
    hotdot_outer_color: int  # u16
    unique_id: int  # u32
    num_guis: int  # u32
    num_cursors: int  # u32
    res_type: ResolutionType  # u32
    resolution: GameSetup.Resolution | None
    lipsync_default_frame: int  # u32
    inv_hotspot_marker_img: int  # u32
    # reserved 17 * 4
    has_game_message: list[bool]  # u32[500]
    load_dictionary: bool  # u32
    global_scr_not_null: bool  # u32
    chars_not_null: bool  # u32
    compiled_scr_not_null: bool  # u32

    @classmethod
    def read(cls, br: ByteReader) -> GameSetup:
        game_name = br.fstr(50)
        br.skip(2)
        options: list[int] = []
        for _ in range(GameSetup.NUM_OPTIONS):
            options.append(br.u32())
        palette_types: list[GameSetup.PaletteType] = []
        for _ in range(GameSetup.NUM_PALETTE_COLORS):
            palette_types.append(GameSetup.PaletteType(br.u8()))
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
        res_type = GameSetup.ResolutionType(br.u32())
        resolution: GameSetup.Resolution | None = None
        if res_type is GameSetup.ResolutionType.CUSTOM:
            w = br.u32()
            h = br.u32()
            resolution = GameSetup.Resolution(w, h)
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
            res_type,
            resolution,
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
        description = br.fstr(25)
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
    class Flag(IntFlag):
        ANIMMOVE = 1
        DISABLED = 2
        STANDARD = 4
        HOTSPOT = 8

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
        name = br.fstr(10)
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


@dataclass
class Script:
    offset: int
    size: int
    name: str

    @classmethod
    def read(cls, br: ByteReader) -> Script:
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


@dataclass
class PluginData:
    file_name: str  # cstr
    offset: int
    size: int  # int

    @classmethod
    def read(cls, br: ByteReader) -> PluginData:
        file_name = br.cstr()
        offset = br.tell()
        size = br.u32()
        br.skip(size)
        return PluginData(file_name, offset, size)


@dataclass
class SchemaItem:
    name: str
    type: int
    description: str
    default: str

    @classmethod
    def read(cls, br: ByteReader) -> SchemaItem:
        return SchemaItem(
            name=br.pstr(),
            type=br.u32(),
            description=br.pstr(),
            default=br.pstr(),
        )


@dataclass
class CustomProperties:
    cprops_ver: int
    props: dict[str, str]

    @classmethod
    def read(cls, br: ByteReader) -> CustomProperties:
        cpver = br.u32()
        props: dict[str, str] = {}
        for _ in range(br.u32()):
            props[br.pstr()] = br.pstr()
        return CustomProperties(cpver, props)


@dataclass
class AudioClipType:
    class CrossfadeSpeed(IntEnum):
        NO = 0
        SLOW = 1
        SLOWISH = 2
        MEDIUM = 3
        FAST = 4

    id: int
    reserved_channels: int
    reduce_volume: bool
    crossfade_speed: CrossfadeSpeed
    # reserved u32

    @classmethod
    def read(cls, br: ByteReader) -> AudioClipType:
        clip = AudioClipType(
            id=br.u32(),
            reserved_channels=br.u32(),
            reduce_volume=bool(br.u32()),
            crossfade_speed=AudioClipType.CrossfadeSpeed(br.u32()),
        )
        br.u32()  # reserved
        return clip


@dataclass
class AudioClip:
    class BundlingType(IntEnum):
        GAME_EXE = 1
        SEPARATE_VOX = 2

    class FileType(IntEnum):
        OGG = 1
        MP3 = 2
        WAV = 3
        VOC = 4
        MIDI = 5
        MOD = 6

    id: int
    script_name: str  # 30
    file_name: str  # 15
    bundling_type: AudioClip.BundlingType  # u8
    type: int  # u8
    file_type: AudioClip.FileType  # u8
    repeat: bool  # u8
    # padding 1
    priority: int  # u8
    volume: int  # u8
    # padding 2
    # reserved 1

    @classmethod
    def read(cls, br: ByteReader) -> AudioClip:
        id_ = br.u32()
        script_name = br.fstr(30)
        file_name = br.fstr(15)
        bundling_type = AudioClip.BundlingType(br.u8())
        type_ = br.u8()
        file_type = AudioClip.FileType(br.u8())
        repeat = bool(br.u8())
        br.skip(1)  # padding
        priority = br.u16()
        volume = br.u16()
        br.skip(2)  # padding
        br.u32()  # reserved

        return AudioClip(
            id=id_,
            script_name=script_name,
            file_name=file_name,
            bundling_type=bundling_type,
            type=type_,
            file_type=file_type,
            repeat=repeat,
            priority=priority,
            volume=volume,
        )


@dataclass
class Room:
    number: int  # u32
    description: str  # cstr

    @classmethod
    def read(cls, br: ByteReader) -> Room:
        return Room(br.u32(), br.cstr())


@dataclass
class Extension:
    type: int  # u8
    ext_id: str  # 16
    size: int  # u64
    offset: int  # tell

    @classmethod
    def read(cls, br: ByteReader) -> Extension:
        type_ = br.u8()
        ext_id = br.fstr(16)
        size = br.u64()
        offset = br.tell()
        br.skip(size)
        return Extension(type_, ext_id, size, offset)


@dataclass
class GameData:
    SIGNATURE: ClassVar = "Adventure Creator Game File v2"

    version: int  # u32
    editor_version: str  # pstr
    extended_engine_caps: int
    setup: GameSetup
    guid: str  # str[40]
    savegame_file_ext: str  # str[20]
    savegame_folder: str  # str[50]
    fonts: list[Font]
    topmost_sprite: int  # u32
    sprite_flags: list[int]
    inventory_items: list[InventoryItem]
    cursors: list[Cursor]
    char_interact_scripts: list[InteractionScript]
    invitem_inter_scr: list[InteractionScript]
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
    guis: GameGuis
    plugins_ver: int
    plugin_data: list[PluginData]
    custom_prop_ver: int
    schemas: list[SchemaItem]
    char_cprops: list[CustomProperties]
    item_cprops: list[CustomProperties]
    view_names: list[str]  # cstr
    item_names: list[str]  # cstr
    dialog_names: list[str]  # cstr
    audio_clip_types: list[AudioClipType]
    audio_clips: list[AudioClip]
    play_sound_on_score: int  # u32
    rooms: list[Room]
    fonts_ext: Extension
    cursors_ext: Extension

    @classmethod
    def read(cls, br: ByteReader) -> GameData:
        signature = br.fstr(len(GameData.SIGNATURE))
        check(signature == GameData.SIGNATURE, "game data file signature mismatch")
        version = br.u32()
        editor_version = br.pstr()
        extended_engine_caps = br.u32()
        gs = GameSetup.read(br)
        guid = br.fstr(40)
        save_game_file_ext = br.fstr(20)
        save_game_folder_name = br.fstr(50)
        fonts = [Font.read(br) for _ in range(gs.num_fonts)]
        topmost_sprite = br.u32() - 1
        sprite_flags = [br.u8() for _ in range(topmost_sprite + 1)]
        br.skip(68)  # unused inventory item slot 0
        inventory_items = [InventoryItem.read(br) for _ in range(gs.num_invitems)]
        cursors = [Cursor.read(br) for _ in range(gs.num_cursors)]
        char_inter_scr = [InteractionScript.read(br) for _ in range(gs.num_chars)]
        invitem_inter_scr = [InteractionScript.read(br) for _ in range(gs.num_invitems)]
        parser_words = [ParserWord.read(br) for _ in range(br.u32())]
        global_script = Script.read(br)
        dialog_script = Script.read(br)
        num_scripts = br.u32()
        scripts: list[Script] = [Script.read(br) for _ in range(num_scripts)]
        views: list[View] = [View.read(br) for _ in range(gs.num_views)]
        characters: list[Character] = [Character.read(br) for _ in range(gs.num_chars)]
        lipsync = [br.fstr(50) for _ in range(20)]
        global_messages: list[str] = []
        for hm in gs.has_game_message:
            if not hm:
                continue
            size = br.u32()
            s = encrypt.decrypt(br.read(size))
            global_messages.append(s)
        dialogs = [Dialog.read(br) for _ in range(gs.num_dialogs)]
        guis = GameGuis.read(br)
        plugins_ver = br.u32()  # plugins version
        plugin_data = [PluginData.read(br) for _ in range(br.u32())]
        custom_prop_ver = br.u32()
        schemas = [SchemaItem.read(br) for _ in range(br.u32())]
        char_cprops = [CustomProperties.read(br) for _ in range(gs.num_chars)]
        br.u32()  # unused inv slot 0 property header
        br.u32()  # num of its props
        item_cprops = [CustomProperties.read(br) for _ in range(gs.num_invitems)]
        view_names = [br.cstr() for _ in range(gs.num_views)]
        br.u8()  # inv slot 0 name
        item_names = [br.cstr() for _ in range(gs.num_invitems)]
        dialog_names = [br.cstr() for _ in range(gs.num_dialogs)]
        audio_clip_types = [AudioClipType.read(br) for _ in range(br.u32())]
        audio_clips = [AudioClip.read(br) for _ in range(br.u32())]
        rooms: list[Room] = []
        if bool(gs.options[GameSetup.Option.DEBUGMODE]):
            rooms = [Room.read(br) for _ in range(br.u32())]
        play_sound_on_score = br.u32()
        fonts_ext = Extension.read(br)
        cursors_ext = Extension.read(br)

        end = br.byte()
        check(end == 255, f"0xFF expected at extensions end, got 0x{end:0X} instead")
        eof = br.byte()
        check(not eof, f"EOF expected, got 0x{eof:0X} instead")

        return GameData(
            version=version,
            editor_version=editor_version,
            extended_engine_caps=extended_engine_caps,
            setup=gs,
            guid=guid,
            savegame_file_ext=save_game_file_ext,
            savegame_folder=save_game_folder_name,
            fonts=fonts,
            topmost_sprite=topmost_sprite,
            sprite_flags=sprite_flags,
            inventory_items=inventory_items,
            cursors=cursors,
            char_interact_scripts=char_inter_scr,
            invitem_inter_scr=invitem_inter_scr,
            parser_words=parser_words,
            global_script=global_script,
            dialog_script=dialog_script,
            scripts=scripts,
            views=views,
            characters=characters,
            lipsync=lipsync,
            dialogs=dialogs,
            guis=guis,
            plugins_ver=plugins_ver,
            plugin_data=plugin_data,
            custom_prop_ver=custom_prop_ver,
            schemas=schemas,
            char_cprops=char_cprops,
            item_cprops=item_cprops,
            view_names=view_names,
            item_names=item_names,
            dialog_names=dialog_names,
            audio_clip_types=audio_clip_types,
            audio_clips=audio_clips,
            play_sound_on_score=play_sound_on_score,
            rooms=rooms,
            fonts_ext=fonts_ext,
            cursors_ext=cursors_ext,
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_index(self, sw: StringWriter | None = None) -> str:
        if sw is None:
            sw = StringWriter()

        sw.println("=== AGS Game Asset Index ===")
        sw.println(f"Version: {self.version}")
        sw.println(f"Editor version: {self.editor_version}")
        sw.println(f"Game name: {self.setup.game_name}")
        sw.println(f"Game unique ID: {self.setup.unique_id}")
        sw.println(f"Savegame extension: {self.savegame_file_ext}")
        sw.println(f"Savegame folder: {self.savegame_folder}")
        sw.println(f"Total sprites: {self.topmost_sprite}")

        sw.print("Game resolution: ")
        sw.print(self.setup.res_type.name.lower().removeprefix("r"))
        if self.setup.res_type is GameSetup.ResolutionType.CUSTOM:
            sw.print(f" ({self.setup.resolution})")
        sw.println()
        sw.println()

        sw.println("Options:")
        sw.indent()
        sw.println(
            ", ".join(
                f"{o.name}={self.setup.options[o.value]}" for o in GameSetup.Option
            )
        )
        sw.dedent()
        sw.println()

        sw.println("Inventory items:")
        sw.indent()
        for scr_name, item in zip(self.item_names, self.inventory_items):
            sw.println(f"- {item.description} ({scr_name})")
        sw.dedent()
        sw.println()

        sw.println("Characters:")
        sw.indent()
        for c in self.characters:
            sw.println(f"{c.name} ({c.scr_name}):")
            sw.indent()
            sw.println(f"- starting room = {c.starting_room}")
            sw.println(f"- view = {c.view}")
            sw.println(f"- default view = {c.default_view}")
            sw.println(f"- talk view = {c.talk_view}")
            sw.println(f"- think view = {c.think_view}")
            sw.println(f"- blink view = {c.blink_view}")
            sw.println(f"- blink interval = {c.blink_interval}")
            sw.println(f"- idle view = {c.talk_view}")
            sw.println(f"- idle delay = {c.idle_delay}")
            sw.println(f"- idle anim speed = {c.idle_anim_speed}")
            sw.println(f"- walk speed x = {c.walk_speed}")
            sw.println(f"- walk speed y = {c.walk_speed_y}")
            sw.println(f"- walk wait = {c.walk_wait}")
            sw.println(f"- talk color = {c.talk_color}")
            sw.println(f"- blocking width = {c.blocking_width}")
            sw.println(f"- blocking height = {c.blocking_height}")
            sw.dedent()
        sw.dedent()
        sw.println()

        sw.println("Cursors:")
        sw.indent()
        for c in self.cursors:
            sw.println(
                f"- {c.name}, image={c.image}, hotx={c.hotspot_x}, hoty={c.hotspot_y}"
            )
        sw.dedent()
        sw.println()

        sw.println("Views:")
        sw.indent()
        for name, view in zip(self.view_names, self.views):
            sw.println(f"- {name} ({len(view.loops)} loops)")
            sw.indent()
            for li, l in enumerate(view.loops):
                sw.println(f"- {li} (run next = {l.run_next_loop})")
                sw.indent()
                for f in l.frames:
                    sw.println(f"- {f.image}, flipped={f.flipped}, delay={f.delay}")
                sw.dedent()
            sw.dedent()
        sw.dedent()
        sw.println()

        sw.println("Dialogs:")
        sw.indent()
        for name, dlg in zip(self.dialog_names, self.dialogs):
            sw.println(f"- {name}")
            sw.indent()
            for op in dlg.options:
                sw.println(f"- {op}")
            sw.dedent()
        sw.dedent()

        sw.println("Schema items:")
        sw.indent()
        for s in self.schemas:
            sw.println(f"- {s.name} ({s.type}): {s.description}")
        sw.dedent()
        sw.println()

        sw.println("Audio clips:")
        sw.indent()
        for c in self.audio_clips:
            sw.println(f"- {c.script_name} ({c.file_name}) {c.volume}%")
        sw.dedent()

        return str(sw)
