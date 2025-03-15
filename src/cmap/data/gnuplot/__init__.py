"""Color schemes from gnuplot.

https://gnuplot.sourceforge.net

/*[
 * Copyright 1986 - 1993, 1998, 2004   Thomas Williams, Colin Kelley
 *
 * Permission to use, copy, and distribute this software and its
 * documentation for any purpose with or without fee is hereby granted,
 * provided that the above copyright notice appear in all copies and
 * that both that copyright notice and this permission notice appear
 * in supporting documentation.
 *
 * Permission to modify the software is granted, but not the right to
 * distribute the complete modified source code.  Modifications are to
 * be distributed as patches to the released version.  Permission to
 * distribute binaries produced by compiling modified sources is granted,
 * provided you
 *   1. distribute the corresponding source modifications from the
 *    released version in the form of a patch file along with the binaries,
 *   2. add special version identification to distinguish your version
 *    in addition to the base release version number,
 *   3. provide your name and address as the primary contact for the
 *    support of your modified version, and
 *   4. retain our contact information in regard to use of the base
 *    software.
 * Permission to distribute the released version of the source code along
 * with corresponding source modifications in the form of a patch file is
 * granted with same provisions 2 through 4 for binary distributions.
 *
 * This software is provided "as is" without express or implied warranty
 * to the extent permitted by applicable law.
]*/

#### GNUPLOT RGB FORMULAE ########################################

# List of palette functions in Gnuplot (show palette rgbformulae).
# Note that "180x" corresponds to pi*x etc. since built-in trig
# functions use radians.
#   00: 0              01: 0.5            02: 1
#   03: x              04: x^2            05: x^3
#   06: x^4            07: sqrt(x)        08: sqrt(sqrt(x))
#   09: sin(90x)       10: cos(90x)       11: |x-0.5|
#   12: (2x-1)^2       13: sin(180x)      14: |cos(180x)|
#   15: sin(360x)      16: cos(360x)      17: |sin(360x)|
#   18: |cos(360x)|    19: |sin(720x)|    20: |cos(720x)|
#   21: 3x             22: 3x-1           23: 3x-2
#   24: |3x-1|         25: |3x-2|         26: (3x-1)/2
#   27: (3x-2)/2       28: |(3x-1)/2|     29: |(3x-2)/2|
#   30: x/0.32-0.78125 31: 2*x-0.84       32: 4x;1;-2x+1.84;x/0.08-11.5
#   33: |2*x - 0.5|    34: 2*x            35: 2*x - 0.5
#   36: 2*x - 1
"""

from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from typing import Callable

    from numpy.typing import NDArray
    from typing_extensions import TypeAlias

    ArrayMapper: TypeAlias = Callable[[NDArray], NDArray]


# fmt: off
# commented out ones just aren't used at the moment.
# def _g0(x): return np.zeros_like(x)
# def _g1(x): return 0.5 * np.ones_like(x)
def _g2(x): return np.ones_like(x)
def _g3(x): return x
# def _g4(x): return x ** 2
def _g5(x): return x ** 3
def _g6(x): return x ** 4
def _g7(x): return np.sqrt(x)
# def _g8(x): return np.sqrt(np.sqrt(x))
# def _g9(x): return np.sin(x * np.pi / 2)
def _g10(x): return np.cos(x * np.pi / 2)
def _g11(x): return np.abs(x - 0.5)
# def _g12(x): return (2 * x - 1) ** 2
def _g13(x): return np.sin(x * np.pi)
# def _g14(x): return np.abs(np.cos(x * np.pi))
def _g15(x): return np.sin(x * 2 * np.pi)
# def _g16(x): return np.cos(x * 2 * np.pi)
# def _g17(x): return np.abs(np.sin(x * 2 * np.pi))
# def _g18(x): return np.abs(np.cos(x * 2 * np.pi))
# def _g19(x): return np.abs(np.sin(x * 4 * np.pi))
# def _g20(x): return np.abs(np.cos(x * 4 * np.pi))
def _g21(x): return 3 * x
def _g22(x): return 3 * x - 1
def _g23(x): return 3 * x - 2
# def _g24(x): return np.abs(3 * x - 1)
# def _g25(x): return np.abs(3 * x - 2)
# def _g26(x): return (3 * x - 1) / 2
# def _g27(x): return (3 * x - 2) / 2
def _g28(x): return np.abs((3 * x - 1) / 2)
# def _g29(x): return np.abs((3 * x - 2) / 2)
def _g30(x): return x / 0.32 - 0.78125
def _g31(x): return 2 * x - 0.84
def _g32(x):
    ret = np.zeros(len(x))
    m = (x < 0.25)
    ret[m] = 4 * x[m]
    m = (x >= 0.25) & (x < 0.92)
    ret[m] = -2 * x[m] + 1.84
    m = (x >= 0.92)
    ret[m] = x[m] / 0.08 - 11.5
    return ret
def _g33(x): return np.abs(2 * x - 0.5)
def _g34(x): return 2 * x
def _g35(x): return 2 * x - 0.5
def _g36(x): return 2 * x - 1
# fmt: on


def _combine_gnufunc(mappers: Sequence["ArrayMapper"], ary: "NDArray") -> "NDArray":
    """Combine multiple gnuplot formulae."""
    return np.stack([_g(np.asarray(ary)) for _g in mappers], axis=-1)


def _combine_gnufunc_hsv(mappers: Sequence["ArrayMapper"], ary: "NDArray") -> "NDArray":
    """Combine multiple gnuplot formulae in hsv space."""
    from cmap._util import hsv_to_rgb

    return hsv_to_rgb(_combine_gnufunc(mappers, ary))


# https://web.mit.edu/gnuplot_v4.2/doc/htmldocs/node216.html
# Some nice schemes in RGB color space

#   7,5,15   ... traditional pm3d (black-blue-red-yellow)
gnuplot = partial(_combine_gnufunc, (_g7, _g5, _g15))
#   3,11,6   ... green-red-violet
grv = partial(_combine_gnufunc, (_g3, _g11, _g6))
#   23,28,3  ... ocean (green-blue-white); try also all other permutations
ocean = partial(_combine_gnufunc, (_g23, _g28, _g3))
#   21,22,23 ... hot (black-red-yellow-white)
hot = partial(_combine_gnufunc, (_g21, _g22, _g23))
#   30,31,32 ... color printable on gray (black-blue-violet-yellow-white)
gnuplot2 = partial(_combine_gnufunc, (_g30, _g31, _g32))
#   33,13,10 ... rainbow (blue-green-yellow-red)
rainbow = partial(_combine_gnufunc, (_g33, _g13, _g10))
#   34,35,36 ... AFM hot (black-red-yellow-white)
afmhot = partial(_combine_gnufunc, (_g34, _g35, _g36))

# A full color palette in HSV color space
# 3,2,2    ... red-yellow-green-cyan-blue-magenta-red
hsv = partial(_combine_gnufunc_hsv, (_g3, _g2, _g2))
