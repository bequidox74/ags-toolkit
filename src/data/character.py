from dataclasses import dataclass

from _internal.byte_reader import ByteReader


@dataclass
class Character:
    default_view: int  # u32
    talk_view: int  # u32
    view: int  # u32
    starting_room: int  # u32
    prev_room: int  # u32 (runtime)
    x: int  # i32
    y: int  # i32
    wait: int  # u32
    flags: int  # u32
    following: int  # u16
    follow_info: int  # u16
    idle_view: int  # u32
    idle_delay: int  # i16
    idle_left: int  # i16 (runtime)
    transparency: int  # i16
    baseline: int  # i16
    active_inv: int  # u32
    talk_color: int  # u32
    think_view: int  # u32
    blink_view: int  # u16
    blink_interval: int  # i16
    blink_timer: int  # i16
    blink_frame: int  # u16
    walk_speed_y: int  # i16
    pic_yoffs: int  # i16
    z: int  # i32
    walk_wait: int  # u32
    speech_anim_speed: int  # i16
    idle_anim_speed: int  # i16
    blocking_width: int  # u16
    blocking_height: int  # u16
    index_id: int  # u32
    pic_xoffs: int  # i16
    walk_wait_counter: int  # u16
    loop: int  # u16
    frame: int  # u16
    walking: int  # u16
    animating: int  # u16
    walk_speed: int  # u16
    anim_speed: int  # u16
    starts_with_item: list[int]  # u8[301]
    act_x: int  # i16
    act_y: int  # i16
    name: str  # 40
    script_name: str  # 20
    on: bool  # u8
    # padding 1

    @classmethod
    def read(cls, br: ByteReader) -> Character:
        default_view = br.i32() + 1
        talk_view = br.i32() + 1
        view = br.i32() + 1
        starting_room = br.u32()
        prev_room = br.u32()
        x = br.i32()
        y = br.i32()
        wait = br.u32()
        flags = br.u32()
        following = br.u16()
        follow_info = br.u16()
        idle_view = br.i32() + 1
        idle_delay = br.i16()
        idle_left = br.i16()
        transparency = br.i16()
        baseline = br.i16()
        active_inv = br.u32()
        talk_color = br.u32()
        think_view = br.i32() + 1
        blink_view = br.i16() + 1
        blink_interval = br.i16()
        blink_timer = br.i16()
        blink_frame = br.u16()
        walk_speed_y = br.i16()
        pic_yoffs = br.i16()
        z = br.i32()
        walk_wait = br.u32()
        speech_anim_speed = br.i16()
        idle_anim_speed = br.i16()
        blocking_width = br.u16()
        blocking_height = br.u16()
        index_id = br.u32()
        pic_xoffs = br.i16()
        walk_wait_counter = br.u16()
        loop = br.u16()
        frame = br.u16()
        walking = br.u16()
        animating = br.u16()
        walk_speed = br.u16()
        anim_speed = br.u16()
        starts_with_item = [br.u16() for _ in range(301)]
        act_x = br.i16()
        act_y = br.i16()
        name = br.string(40)
        script_name = br.string(20)
        on = bool(br.u8())
        br.skip(1)  # padding

        return cls(
            default_view,
            talk_view,
            view,
            starting_room,
            prev_room,
            x,
            y,
            wait,
            flags,
            following,
            follow_info,
            idle_view,
            idle_delay,
            idle_left,
            transparency,
            baseline,
            active_inv,
            talk_color,
            think_view,
            blink_view,
            blink_interval,
            blink_timer,
            blink_frame,
            walk_speed_y,
            pic_yoffs,
            z,
            walk_wait,
            speech_anim_speed,
            idle_anim_speed,
            blocking_width,
            blocking_height,
            index_id,
            pic_xoffs,
            walk_wait_counter,
            loop,
            frame,
            walking,
            animating,
            walk_speed,
            anim_speed,
            starts_with_item,
            act_x,
            act_y,
            name,
            script_name,
            on,
        )
