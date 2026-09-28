from dataclasses import dataclass
from enum import IntFlag
from typing import ClassVar

from _internal.byte_reader import ByteReader
from _internal.utils import check


class GuiFlag(IntFlag):
    CLICKABLE = 1
    TEXT_WINDOW = 2
    VISIBLE = 4
    CONCEAL = 8


class ControlFlag(IntFlag):
    DEFAULT = 1
    CANCEL = 2
    ENABLED = 4
    TAB_STOP = 8
    VISIBLE = 16
    CLIP = 32
    CLICKABLE = 64
    TRANSLATED = 128
    DELETED = 32768


@dataclass
class Gui:
    name: str  # pstr
    on_click: str  # pstr
    left: int  # i32
    top: int  # i32
    width: int  # u32
    height: int  # u32
    num_controls: int  # u32
    popup_style: int  # u32
    popup_ypos: int  # i32
    bgcolor: int  # u32
    bg_img: int  # u32
    border_color: int  # u32
    flags: int  # u32
    transparency: int  # u32
    zorder: int  # u32
    id: int  # u32
    padding: int  # u32  # gui padding, not struct padding
    object_ptrs: list[int]  # u32[num_controls]

    @classmethod
    def read(cls, br: ByteReader) -> Gui:
        name = br.pstr()
        on_click = br.pstr()
        left = br.i32()
        top = br.i32()
        width = br.u32()
        height = br.u32()
        num_controls = br.u32()
        popup_style = br.u32()
        popup_ypos = br.i32()
        bgcolor = br.u32()
        bg_img = br.u32()
        border_color = br.u32()
        flags = br.u32()
        transparency = br.u32()
        zorder = br.u32()
        id_ = br.u32()
        padding = br.u32()
        object_ptrs = [br.u32() for _ in range(num_controls)]

        return Gui(
            name,
            on_click,
            left,
            top,
            width,
            height,
            num_controls,
            popup_style,
            popup_ypos,
            bgcolor,
            bg_img,
            border_color,
            flags,
            transparency,
            zorder,
            id_,
            padding,
            object_ptrs,
        )


@dataclass
class Control:
    flags: int  # u32
    left: int  # i32
    top: int  # i32
    width: int  # u32
    height: int  # u32
    zorder: int  # u32
    name: str  # cstr
    # num_events u32
    events: list[str]

    @classmethod
    def read(cls, br: ByteReader) -> Control:
        flags = br.u32()
        left = br.i32()
        top = br.i32()
        width = br.u32()
        height = br.u32()
        zorder = br.u32()
        name = br.cstr()
        num_events = br.u32()
        events = [br.cstr() for _ in range(num_events)]

        return Control(
            flags,
            left,
            top,
            width,
            height,
            zorder,
            name,
            events,
        )


@dataclass
class Edge:
    # everything u32 by default
    control: Control
    img: int
    mouseover_img: int
    pushed_img: int
    font: int
    text_color: int
    lclick_action: int
    rclick_action: int
    lclick_data: int
    rclick_data: int
    text: str  # pstr
    align: int

    @classmethod
    def read(cls, br: ByteReader) -> Edge:
        return Edge(
            control=Control.read(br),
            img=br.u32(),
            mouseover_img=br.u32(),
            pushed_img=br.u32(),
            font=br.u32(),
            text_color=br.u32(),
            lclick_action=br.u32(),
            rclick_action=br.u32(),
            lclick_data=br.u32(),
            rclick_data=br.u32(),
            text=br.pstr(),
            align=br.u32(),
        )


@dataclass
class Label:
    control: Control
    text: str  # pstr
    font: int
    color: int
    align: int

    @classmethod
    def read(cls, br: ByteReader) -> Label:
        return Label(
            control=Control.read(br),
            text=br.pstr(),
            font=br.u32(),
            color=br.u32(),
            align=br.u32(),
        )


@dataclass
class InventoryWindow:
    control: Control
    char_id: int
    item_width: int
    item_height: int

    @classmethod
    def read(cls, br: ByteReader) -> InventoryWindow:
        return InventoryWindow(
            control=Control.read(br),
            char_id=br.u32(),
            item_width=br.u32(),
            item_height=br.u32(),
        )


@dataclass
class Slider:
    control: Control
    min: int
    max: int
    value: int
    handle_img: int
    handle_offset: int
    bg_img: int

    @classmethod
    def read(cls, br: ByteReader) -> Slider:
        return Slider(
            control=Control.read(br),
            min=br.i32(),
            max=br.i32(),
            value=br.i32(),
            handle_img=br.u32(),
            handle_offset=br.i32(),
            bg_img=br.u32(),
        )


class TextBoxFlag(IntFlag):
    SHOW_BORDER = 1


@dataclass
class TextBox:
    control: Control
    text: str
    font: int
    text_color: int
    flags: int

    @classmethod
    def read(cls, br: ByteReader) -> TextBox:
        return TextBox(
            control=Control.read(br),
            text=br.pstr(),
            font=br.u32(),
            text_color=br.u32(),
            flags=br.u32(),
        )


class ListBoxFlag(IntFlag):
    SHOW_BORDER = 1
    SHOW_ARROWS = 2
    SVG_INDEX = 4


@dataclass
class ListBox:
    control: Control
    num_items: int
    font: int
    text_color: int
    sel_text_color: int
    flags: int
    text_align: int
    sel_bg_color: int

    @classmethod
    def read(cls, br: ByteReader) -> ListBox:
        return ListBox(
            control=Control.read(br),
            num_items=br.u32(),
            font=br.u32(),
            text_color=br.u32(),
            sel_text_color=br.u32(),
            flags=br.u32(),
            text_align=br.u32(),
            sel_bg_color=br.u32(),
        )


@dataclass
class GameGuis:
    MAGIC: ClassVar = 0xCAFEBEEF  # u32

    # magic u32
    version: int  # u32
    # num_guis u32
    guis: list[Gui]
    # num_edges u32
    edges: list[Edge]
    # num_labels u32
    labels: list[Label]
    # num_inv_windows u32
    inv_windows: list[InventoryWindow]
    # num_sliders u32
    sliders: list[Slider]
    # num_text_boxes u32
    text_boxes: list[TextBox]
    # num_list_boxes u32
    list_boxes: list[ListBox]

    @classmethod
    def read(cls, br: ByteReader) -> GameGuis:
        magic = br.u32()
        check(magic == GameGuis.MAGIC)
        version = br.u32()
        num_guis = br.u32()
        guis = [Gui.read(br) for _ in range(num_guis)]
        num_edges = br.u32()
        edges = [Edge.read(br) for _ in range(num_edges)]
        num_labels = br.u32()
        labels = [Label.read(br) for _ in range(num_labels)]
        num_inv_windows = br.u32()
        inv_windows = [InventoryWindow.read(br) for _ in range(num_inv_windows)]
        num_sliders = br.u32()
        sliders = [Slider.read(br) for _ in range(num_sliders)]
        num_text_boxes = br.u32()
        text_boxes = [TextBox.read(br) for _ in range(num_text_boxes)]
        num_list_boxes = br.u32()
        list_boxes = [ListBox.read(br) for _ in range(num_list_boxes)]

        return GameGuis(
            version,
            guis,
            edges,
            labels,
            inv_windows,
            sliders,
            text_boxes,
            list_boxes,
        )
