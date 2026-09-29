from abc import ABC, abstractmethod
from dataclasses import dataclass


class Color(ABC):
    @abstractmethod
    def rgba_bytes(self) -> bytes:
        pass


@dataclass
class ColorRGB(Color):
    r: int
    g: int
    b: int

    @staticmethod
    def from_rgba(rgba: ColorRGBA) -> ColorRGB:
        return ColorRGB(rgba.r, rgba.g, rgba.b)

    def rgba_bytes(self) -> bytes:
        return bytes((self.r, self.g, self.b, 255))


@dataclass
class ColorRGBA(Color):
    r: int
    g: int
    b: int
    a: int

    @classmethod
    def from_rgb(cls, rgb: ColorRGB, a: int = 255) -> ColorRGBA:
        return ColorRGBA(rgb.r, rgb.g, rgb.b, a)

    def rgba_bytes(self) -> bytes:
        return bytes((self.r, self.g, self.b, self.a))


@dataclass
class Slot:
    offset: int
    size: int
