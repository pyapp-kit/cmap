"""Colormaps in vispy/vispy/color/colormap.py.

https://github.com/vispy/vispy/blob/356800a784f0dcb7428aa2ade3c9025a8bc2d5cc/vispy/color/colormap.py
"""

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


# hsv(200/360, 0.1, 1) -> hsv(200/360, 0.8, 1)
light_blues = [(0.9, 0.96666, 1.0), (0.2, 0.733333, 1.0)]
single_hue = light_blues  # just an alias in vispy

# hsv(35/360, 0.1, 1) -> hsv(35/360, 0.8, 1)
orange = [(1.0, 0.9583333, 0.9), (1.0, 0.6666667, 0.2)]

# Diverging(255, 133, 0.75, 0.6),
GrBu = [
    [0.27872962, 0.6301783, 0.35279453],
    [0.92, 0.92, 0.92],
    [0.3919671, 0.5555349, 0.88773626],
]

# Diverging(255, 133, 0.75, 0.6, "dark"),
GrBu_d = [
    [0.27872962, 0.6301783, 0.35279453],
    [0.133, 0.133, 0.133],
    [0.3919671, 0.5555349, 0.88773626],
]

# RdBu=Diverging(220, 20, 0.75, 0.5),
# Note: NAME CONFLICT with colorbrewer
RdBu = [
    [0.75374883, 0.33251518, 0.22683573],
    [0.92, 0.92, 0.92],
    [0.24790125, 0.49360412, 0.56957495],
]


# Diverging(145, 280, 0.85, 0.30),
PuGr = [
    [0.3813749, 0.13527402, 0.6101997],
    [0.92, 0.92, 0.92],
    [0.09278259, 0.31200334, 0.20554015],
]


# Diverging()
diverging = [
    [0.43005887, 0.6724293, 0.9967565],
    [0.92, 0.92, 0.92],
    [0.99753714, 0.53117585, 0.43829587],
]


hsl = [
    [1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0],
    [1.0, 0.0, 1.0],
]

husl = [
    [0.9973474, 0.51224977, 0.62270564],
    [0.8260382, 0.636407, 0.04382102],
    [0.36369213, 0.75049514, 0.04293765],
    [0.05044669, 0.74269027, 0.688584],
    [0.14437217, 0.70164186, 0.9967687],
    [0.92282337, 0.4934482, 0.99669576],
]

# RedYellowBlueCyan()
# "A colormap which goes red-yellow positive and blue-cyan negative"
RdYeBuCy = [
    (0, [0.0, 1.0, 1.0, 1.0]),
    (0.17, [0.0, 0.0, 1.0, 1.0]),
    (0.335, [0.0, 0.0, 1.0, 0.0]),
    (0.665, [1.0, 0.0, 0.0, 0.0]),
    (0.88, [1.0, 0.0, 0.0, 1.0]),
    (1.0, [1.0, 1.0, 0.0, 1.0]),
]


ice = [(0.0, 0.0, 1.0), (1.0, 1.0, 1.0)]  # blue -> white

_white = np.array([1.0, 1.0, 1.0])
_yellow = np.array([1.0, 1.0, 0.0])
_red = np.array([1.0, 0.0, 0.0])


def fire(x: "ArrayLike") -> np.ndarray:
    """Fire colormap function."""
    _x = np.atleast_2d(np.clip(np.asarray(x), 0, 1.0)).T
    c = (1.0 - _x) * _white + _x * _yellow
    e = (1.0 - _x) * _yellow + _x * _red
    return (1.0 - _x) * c + _x * e  # type: ignore
