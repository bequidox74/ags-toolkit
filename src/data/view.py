from dataclasses import dataclass

from _internal.byte_reader import ByteReader


@dataclass
class Frame:
    image: int  # u32
    x_offset: int  # i16
    y_offset: int  # i16
    delay: int  # i16
    # alignment 2
    flipped: bool  # u32
    audio_array_id: int  # u32
    # reserved 2 * 4

    @classmethod
    def read(cls, br: ByteReader) -> Frame:
        image = br.u32()
        x_offset = br.i16()
        y_offset = br.i16()
        delay = br.i16()
        br.skip(2)
        flipped = bool(br.u32())
        audio_array_id = br.u32()
        br.skip(2 * 4)

        return Frame(
            image,
            x_offset,
            y_offset,
            delay,
            flipped,
            audio_array_id,
        )


@dataclass
class Loop:
    # num_frames: int  # u16
    run_next_loop: bool  # u32
    frames: list[Frame]

    @classmethod
    def read(cls, br: ByteReader) -> Loop:
        num_frames = br.u16()
        run_next_loop = bool(br.u32())
        frames = [Frame.read(br) for _ in range(num_frames)]
        return Loop(run_next_loop, frames)


@dataclass
class View:
    # num_loops: int # u16
    loops: list[Loop]

    @classmethod
    def read(cls, br: ByteReader) -> View:
        num_loops = br.u16()
        loops = [Loop.read(br) for _ in range(num_loops)]
        return View(loops)
