from __future__ import annotations

from typing import Tuple


class Color(int):
    @property
    def hex(self):
        return f"#{self.int:06X}"

    @property
    def int(self):
        return int(self)

    @property
    def rgb(self):
        return ((self & 0xFF0000) >> 16, (self & 0x00FF00) >> 8, self & 0x0000FF)

    def __str__(self) -> str:
        return self.hex

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.int})"

    @classmethod
    def from_hex(cls, hex: str) -> Color:
        return cls(hex.lstrip("#"), 16)

    @classmethod
    def from_rgb(cls, rgb: Tuple[int, int, int]) -> Color:
        return cls(rgb[0] << 16 | rgb[1] << 8 | rgb[2])


# Official Color Palette
Color.BLURPLE = Color(5793266)
Color.GREYPLE = Color(10070709)
Color.DARK_BUT_NOT_BLACK = Color(2895667)
Color.NOT_QUITE_BLACK = Color(2303786)
Color.GREEN = Color(5763719)
Color.YELLOW = Color(16705372)
Color.FUSCHIA = Color(15418782)
Color.RED = Color(15548997)
Color.WHITE = Color(16777215)
Color.BLACK = Color(2303786)


# Other Colors
Color.AQUA = Color(1752220)
Color.DARK_AQUA = Color(1146986)
Color.DARK_GREEN = Color(2067276)
Color.BLUE = Color(3447003)
Color.DARK_BLUE = Color(2123412)
Color.PURPLE = Color(10181046)
Color.DARK_PURPLE = Color(7419530)
Color.LUMINOUS_VIVID_PINK = Color(15277667)
Color.DARK_VIVID_PINK = Color(11342935)
Color.GOLD = Color(15844367)
Color.DARK_GOLD = Color(12745742)
Color.ORANGE = Color(15105570)
Color.DARK_ORANGE = Color(11027200)
Color.DARK_RED = Color(10038562)
Color.GREY = Color(9807270)
Color.DARK_GREY = Color(9936031)
Color.DARKER_GREY = Color(8359053)
Color.LIGHT_GREY = Color(12370112)
Color.NAVY = Color(3426654)
Color.DARK_NAVY = Color(2899536)
