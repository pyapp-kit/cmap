from __future__ import annotations

import colorsys
import contextlib
import re
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    NamedTuple,
    Sequence,
    SupportsFloat,
    cast,
    overload,
)

import numpy as np

from . import _external

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Union

    import numpy.typing as npt
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema
    from typing_extensions import TypeAlias

    # not used internally... but available for typing
    RGBTuple: TypeAlias = "tuple[int, int, int] | tuple[float, float, float]"
    RGBATuple: TypeAlias = (
        "tuple[int, int, int, float] | tuple[float, float, float, float]"
    )
    # all of the valid argument types that can be cast to a color
    ColorLike: TypeAlias = Union[
        None,  # casts to transparent
        str,  # color name, hex, 'rgba(r,g,b,a)' or 'hsla(h,s,l,a)' string
        RGBTuple,  # 3-tuple of all ints or all floats
        RGBATuple,  # 4-tuple of all floats, or 3 ints and 1 float
        np.ndarray,  # 3- or 4-element rgb(a) vector
        list[float | int],  # 3- or 4-element rgb(a) vector
        "Color",  # another color object
    ]

# Tuples


class HSVA(NamedTuple):
    h: float
    s: float
    v: float
    a: float = 1

    def to_rgba(self) -> RGBA:
        """Convert to RGB."""
        return RGBA(*colorsys.hsv_to_rgb(self.h, self.s, self.v), self.a)


class HSLA(NamedTuple):
    """Hue, Saturation, Lightness.

    All values are floats between 0 and 1.
    """

    h: float
    s: float
    l: float  # noqa: E741
    a: float = 1

    def to_rgba(self) -> RGBA:
        """Convert to RGB."""
        return RGBA(*colorsys.hls_to_rgb(self.h, self.l, self.s), self.a)

    def in_degrees(self) -> tuple[float, float, float, float]:
        """Convert to degrees."""
        return (self.h * 360, self.s, self.l, self.a)


class RGBA(NamedTuple):
    """RGBA color tuple, all values are floats between 0 and 1."""

    r: float
    g: float
    b: float
    a: float = 1

    @classmethod
    def parse(cls, value: Any) -> RGBA:
        return parse_rgba(value)

    def to_8bit(self) -> RGBA8:
        """Convert to 8-bit integer form."""
        # not performing min/max checks here
        r, g, b = (round(x * 255) for x in (self.r, self.g, self.b))
        return RGBA8(r, g, b, self.a)

    def to_hex(self) -> str:
        """Convert to hex color."""
        return self.to_8bit().to_hex()

    def to_hsv(self) -> HSVA:
        """Convert to Hue, Saturation, Value."""
        return HSVA(*colorsys.rgb_to_hsv(self.r, self.g, self.b), self.a)

    def to_hsl(self) -> HSLA:
        """Convert to Hue, Saturation, Lightness."""
        h, ll, s = colorsys.rgb_to_hls(self.r, self.g, self.b)
        return HSLA(h, s, ll, self.a)

    def __str__(self) -> str:
        return self.to_hex()


class RGBA8(NamedTuple):
    """8 bit RGBA color tuple, where RGB values are from 0 to 255, alpha from 0 to 1."""

    r: int
    g: int
    b: int
    a: float = 1

    @classmethod
    def parse(cls, value: Any) -> RGBA8:
        return parse_rgba(value).to_8bit()

    def to_float(self) -> RGBA:
        """Convert to float."""
        return RGBA(self.r / 255, self.g / 255, self.b / 255, self.a)

    def to_hex(self) -> str:
        """Convert to hex color."""
        out = f"#{self.r:02X}{self.g:02X}{self.b:02X}"
        return f"{out}{round(self.a*255):02X}" if self.a != 1 else out

    def to_hsv(self) -> HSVA:
        """Convert to Hue, Saturation, Value."""
        return self.to_float().to_hsv()

    def to_hsl(self) -> HSLA:
        """Convert to Hue, Saturation, Lightness."""
        return self.to_float().to_hsl()

    def __str__(self) -> str:
        return self.to_hex()

    def rgba_string(self) -> str:
        """Return a string representation of the color."""
        if self.a == 1:
            return f"rgb({self.r}, {self.g}, {self.b})"
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a})"


# regexes for parsing color strings
_num = r"(-?\d+\.?\d*|none)"  # a number or the string 'none'
_perc = r"(-?\d+\.?\d*%|none)"  # a percentage or the string 'none'
_nump = r"(-?\d+\.?\d*%?|none)"  # a number or percentage or the string 'none'
# parse an rgb(a) string
reRGB = re.compile(rf"rgba?\(\s*{_nump}[,\s]+{_nump}[,\s]+{_nump}[,\s/]*{_nump}?\)")
# parse an hsl(a) string
reHSL = re.compile(rf"hsla?\(\s*{_num}[,\s]+{_perc}[,\s]+{_perc}[,\s/]*{_nump}?\)")
# used to strip delimiter characters from color strings with `delim.sub("", name)`
delim = re.compile(r"( |-|_)", re.I)


def _parse_rgb_string(rgb: str) -> RGBA8 | None:
    """Parse a string containing an RGB color into a tuple.

    Parameters
    ----------
    rgb : str
        A string containing an RGB color, e.g. "rgb(2, 3, 4)" or "rgba(2, 3, 4, 0.5)".

    Returns
    -------
    tuple
        A 3 or 4 tuple containing the RGB color where the first three values are
        integers between 0 and 255 and the last value is a float between 0 and 1.

    Examples
    --------
    >>> parse_rgb("rgb(2, 3, 4)")
    (2, 3, 4)
    >>> parse_rgb("rgb(100%, 0%, 0%)")
    (255, 0, 0)
    >>> parse_rgb("rgba(2, 3, 4, 0.5)")
    (2, 3, 4, 0.5)
    >>> parse_rgb("rgba(2, 3, 4, 50%)")
    (2, 3, 4, 0.5)
    >>> parse_rgb("rgb(-2, 3, 4)")
    (0, 3, 4)
    >>> parse_rgb("rgb(100, 200, 300)")
    (100, 200, 255)
    >>> parse_rgb("rgb(20, 10, 0, -10)")
    (20, 10, 0, 0)
    >>> parse_rgb("rgb(100%, 200%, 300%)")
    (255, 255, 255)
    """
    m = reRGB.match(rgb)
    if not m:
        return None
    out = []
    for n, val in enumerate(m.groups()):
        if val is None and n == 3:  # no alpha
            break
        if val in (None, "none"):
            val = 0
        elif val.endswith("%"):
            val = float(val[:-1]) / 100
            if n < 3:
                val = round(val * 255)
        else:
            val = float(val)
            val = round(val) if n < 3 else min(1, max(0, val))
        out.append(min(255, max(0, val)))
    return RGBA8(*out)  # type: ignore


def _parse_hsl_string(hsl: str) -> HSLA | None:
    """Parse a string containing an HSL color into a tuple.

    Parameters
    ----------
    hsl : str
        A string containing an HSL color, e.g. "hsl(0, 100%, 50%)"

    Returns
    -------
    HSLA
        An HSLA named tuple, all values are floats between 0 and 1.
    """
    m = reHSL.match(hsl)
    if not m:  # pragma: no cover
        return None
    out = []
    for n, val in enumerate(m.groups()):
        if val is None and n == 3:  # no alpha
            break
        if val in (None, "none"):
            val = 0
        elif val.endswith("%"):
            val = float(val[:-1]) / 100
        else:
            val = float(val)
            # the hue is a circle expressed in degrees,
            # the other values are percentages
            val = val % 360 / 360 if n == 0 else min(1, max(0, val))
        out.append(val)
    return HSLA(*out)


def _parse_hex_string(hex: str) -> RGBA8:
    """Convert hex color to RGB."""
    _hex = hex.lstrip("#")
    if _hex.startswith("0x"):
        _hex = _hex[2:]
    if len(_hex) == 3:
        _hex = "".join(2 * s for s in _hex)
    if len(_hex) not in (6, 8):
        raise ValueError(f"Input #{hex} is not in #RRGGBB or #RGB format")
    r, g, b, *_a = (int(_hex[i : i + 2], 16) for i in range(0, len(_hex), 2))
    a = max(0, min(1, _a[0] / 255)) if _a else 1
    return RGBA8(r, g, b, a)


# fmt: off
@overload
def _bound_0_1(values: SupportsFloat) -> float: ...
@overload
def _bound_0_1(values: Sequence[SupportsFloat]) -> Sequence[float]: ...
def _bound_0_1(
    values: SupportsFloat | Sequence[SupportsFloat],
) -> float | Sequence[SupportsFloat]:
    # round here?
    return np.clip(values, 0, 1).astype(float)  # type: ignore
# fmt: on


def _bound_0_255(values: Iterable[SupportsFloat]) -> Iterable[int]:
    return (max(0, min(255, round(float(v)))) for v in values)


def _norm_name(name: str) -> str:
    return delim.sub("", name).lower()


def parse_rgba(value: Any) -> RGBA:
    """Parse a color."""
    # parse hex, rgb, rgba, hsl, hsla, and color name strings
    if isinstance(value, str):
        key = _norm_name(value)
        if key in NAME_TO_RGB:
            rgbai = NAME_TO_RGB[key]
            return rgbai.to_float()
        with contextlib.suppress(ValueError):
            return _parse_hex_string(value).to_float()
        if m := _parse_rgb_string(value):
            return m.to_float()
        if h := _parse_hsl_string(value):
            return h.to_rgba()
        raise ValueError(f"Invalid color string: {value!r}")

    # parse tuples/lists/arrays
    if isinstance(value, np.ndarray):
        # val = tuple(np.squeeze(tuple(value)))
        if np.issubdtype(value.dtype, np.integer) and len(value) == 3:
            return RGBA8(*_bound_0_255(value)).to_float()
        if np.issubdtype(value.dtype, np.floating) and len(value) in {3, 4}:
            return RGBA(*_bound_0_1(cast("Sequence", value)))
        raise ValueError(f"Invalid color array: {value!r}")  # pragma: no cover

    if isinstance(value, Sequence):
        if isinstance(value, RGBA):
            return value
        if isinstance(value, RGBA8):
            return value.to_float()
        if all(isinstance(v, int) for v in value[:3]):
            r, g, b = _bound_0_255(value[:3])
            a = _bound_0_1(value[3]) if len(value) > 3 else 1
            return RGBA8(r, g, b, a).to_float()
        return RGBA(*_bound_0_1(value))

    # None is transparent
    if value is None:
        return RGBA(0, 0, 0, 0)

    # support our own Color class

    if isinstance(value, Color):
        return value._rgba

    if isinstance(value, int):
        # convert 24-bit integer to RGBA8 with bit shifting
        r = (value >> 16) & 0xFF
        g = (value >> 8) & 0xFF
        b = value & 0xFF
        return RGBA8(r, g, b).to_float()

    # support for pydantic.color.Color
    for mod in ("pydantic", "pydantic_extra_types"):
        if (pydantic_color := sys.modules.get(f"{mod}.color")) and isinstance(
            value, pydantic_color.Color
        ):
            r, g, b, *alpha = value.as_rgb_tuple()
            return RGBA(r / 255, g / 255, b / 255, alpha[0] if alpha else 1)

    # support for colour.Color
    colour_color = sys.modules.get("colour")
    if colour_color and isinstance(value, colour_color.Color):
        return RGBA(*_bound_0_1(value.get_rgb()))

    raise TypeError(f"Cannot convert type {type(value)!r} to Color")


_COLOR_CACHE: dict[RGBA, Color] = {}


class Color:
    """Class to represent a single color.

    Instances of this class are immutable and cached (based on the rgba tuple),
    you can compare them with `is`.

    Parameters
    ----------
    value : str, tuple, list, array, Color, or int
        The color to represent.  Can be any "ColorLike".
    """

    __slots__ = ("_rgba", "_name", "__weakref__")
    _rgba: RGBA
    _name: str | None

    def __new__(cls, value: Any) -> Color:
        rgba = parse_rgba(value)
        if rgba not in _COLOR_CACHE:
            name = RGB_TO_NAME.get(rgba.to_8bit())
            obj = super().__new__(cls)
            object.__setattr__(obj, "_rgba", rgba)
            object.__setattr__(obj, "_name", name)
            _COLOR_CACHE[rgba] = obj
        return _COLOR_CACHE[rgba]

    # for mkdocstrings
    def __init__(self, value: ColorLike) -> None:
        pass

    # required because of the __new__ implementation, which requires an argument
    # https://docs.python.org/3/library/pickle.html#module-pickle
    # also works for copy and deepcopy
    def __reduce__(self) -> tuple:
        return (self.__class__, (self._rgba,))

    def __setattr__(self, __name: str, __value: Any) -> None:
        raise AttributeError("Color is immutable")

    # len and getitem are required for proper handling when casting
    # a list of colors to an array (e.g. np.array([Color('red'), Color('blue')]))

    def __len__(self) -> int:
        return 4

    def __getitem__(self, key: int) -> float:
        return self._rgba[key]

    def __iter__(self) -> Iterator[float]:
        return iter(self._rgba)

    def __array__(self, dtype: npt.DTypeLike = None) -> np.ndarray:
        return np.asarray(self._rgba, dtype=dtype)

    @property
    def alpha(self) -> float:
        """Return the alpha value."""
        return self._rgba[3]

    @property
    def hsl(self) -> HSLA:
        """Return the color as Hue, Saturation, Lightness."""
        return self._rgba.to_hsl()

    @property
    def hsv(self) -> HSVA:
        """Return the color as Hue, Saturation, Value."""
        return self._rgba.to_hsv()

    @property
    def rgba(self) -> RGBA:
        """Return the color as (Red, Green, Blue, Alpha) tuple in 0-1 range."""
        return self._rgba

    @property
    def rgba8(self) -> RGBA8:
        """Return the color as (Red, Green, Blue, Alpha) tuple in 0-255 range."""
        return self._rgba.to_8bit()

    @property
    def rgba_string(self) -> str:
        """Return the color as an 'rgba(r, g, b, a)' string; 0-255 range."""
        return self.rgba8.rgba_string()

    @property
    def hex(self) -> str:
        """Return the color as hex."""
        return self._rgba.to_hex()

    @property
    def name(self) -> str | None:
        """Return the color as name."""
        return self._name

    def __hash__(self) -> int:
        return hash(self._rgba)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Color):
            return self._rgba == __o._rgba
        try:
            return self._rgba == parse_rgba(__o)
        except TypeError:
            return NotImplemented

    def __str__(self) -> str:
        """Return a string representation of the color."""
        return self.name or self.hex

    def __repr__(self) -> str:
        """Return a string representation of the color."""
        if self.name:
            arg: str | tuple = self.name
        else:
            arg = tuple(round(x, 4) for x in tuple(self._rgba))
            if self._rgba.a == 1:
                arg = arg[:3]
        return f"{self.__class__.__name__}({arg!r})"

    def __rich_repr__(self) -> Any:
        """Provide a rich representation of the color, with color swatch."""
        return _external.rich_print_color(self)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from pydantic_core import core_schema

        schema = handler(Any)
        return core_schema.no_info_after_validator_function(cls, schema)

    @classmethod
    def __get_validators__(cls) -> Iterator[Callable]:
        yield cls  # pydantic validator

    def _json_encode(self) -> str:
        # psygnal.EventedModel support
        return str(self)


ALL_COLORS: dict[str, tuple[int, ...]] = {
    # https://www.w3.org/TR/CSS1/
    "black": (0, 0, 0),
    "k": (0, 0, 0),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "silver": (192, 192, 192),
    "white": (255, 255, 255),
    "w": (255, 255, 255),
    "maroon": (128, 0, 0),
    "red": (255, 0, 0),
    "r": (255, 0, 0),
    "purple": (128, 0, 128),
    "fuchsia": (255, 0, 255),
    "magenta": (255, 0, 255),
    "m": (255, 0, 255),
    "green": (0, 128, 0),
    "lime": (0, 255, 0),
    "g": (0, 255, 0),
    "olive": (128, 128, 0),
    "yellow": (255, 255, 0),
    "y": (255, 255, 0),
    "navy": (0, 0, 128),
    "blue": (0, 0, 255),
    "b": (0, 0, 255),
    "teal": (0, 128, 128),
    "aqua": (0, 255, 255),
    "cyan": (0, 255, 255),
    "c": (0, 255, 255),
    # https://www.w3.org/TR/CSS2/
    "orange": (255, 165, 0),
    # https://drafts.csswg.org/css-color-3/
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 235, 215),
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "blanchedalmond": (255, 235, 205),
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgrey": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0),
    "goldenrod": (218, 165, 32),
    "greenyellow": (173, 255, 47),
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lavenderblush": (255, 240, 245),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "oldlace": (253, 245, 230),
    "olivedrab": (107, 142, 35),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "rebeccapurple": (102, 51, 153),
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "whitesmoke": (245, 245, 245),
    "yellowgreen": (154, 205, 50),
    "transparent": (0, 0, 0, 0),
    "none": (0, 0, 0, 0),
}
NAME_TO_RGB = {name: RGBA8(*values) for name, values in ALL_COLORS.items()}
RGB_TO_NAME = {v: name for name, v in NAME_TO_RGB.items()}
# for a few names with aliases... make sure the canonical name is used
RGB_TO_NAME[RGBA8(255, 0, 0)] = "red"
RGB_TO_NAME[RGBA8(0, 255, 0)] = "lime"  # unfortunate, but true
RGB_TO_NAME[RGBA8(0, 0, 255)] = "blue"
RGB_TO_NAME[RGBA8(255, 255, 0)] = "yellow"
RGB_TO_NAME[RGBA8(0, 255, 255)] = "cyan"
RGB_TO_NAME[RGBA8(255, 0, 255)] = "magenta"
RGB_TO_NAME[RGBA8(128, 128, 128)] = "gray"
RGB_TO_NAME[RGBA8(0, 0, 0)] = "black"
RGB_TO_NAME[RGBA8(255, 255, 255)] = "white"
