# glasbey vendored from https://github.com/lmcinnes/glasbey.
# see __init__ and LICENSE_GLASBEY
from __future__ import annotations

from collections.abc import Sized

import numpy as np


def _cspace_convert(arr: np.ndarray, start: str | dict, end: str) -> np.ndarray:
    from colorspacious import cspace_convert

    return cspace_convert(arr, start, end)  # type: ignore


def _norm_gridsize(grid_size: int | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(grid_size, int):
        return (grid_size, grid_size, grid_size)
    elif isinstance(grid_size, Sized) and len(grid_size) == 3:
        return grid_size
    raise ValueError(  # pragma: no cover
        "Parameter grid_size should either be an integer or a 3-tuple of integers"
    )


def rgb_grid(
    grid_size: int | tuple[int, int, int] = 64,
    red_bounds: tuple[float, float] = (0, 1),
    green_bounds: tuple[float, float] = (0, 1),
    blue_bounds: tuple[float, float] = (0, 1),
    output_colorspace: str = "sRGB1",
) -> np.ndarray:
    """Return an (grid_size.size, 3) grid of points regularly sampled from RGB space."""
    g0, g1, g2 = _norm_gridsize(grid_size)
    r = np.repeat(np.linspace(*red_bounds, g0), g1 * g2)
    g = np.tile(np.repeat(np.linspace(*green_bounds, g1), g2), g0)
    b = np.tile(np.linspace(*blue_bounds, g2), g0 * g1)
    colors = np.vstack([r, g, b]).T

    if output_colorspace != "sRGB1":
        colors = _cspace_convert(colors, "sRGB1", output_colorspace)
    return colors.astype(np.float32, order="C")


def jch_grid(
    grid_size: int | tuple[int, int, int] = 64,
    lightness_bounds: tuple[float, float] = (10, 90),
    chroma_bounds: tuple[float, float] = (10, 90),
    hue_bounds: tuple[float, float] = (0, 360),
    output_colorspace: str = "JCh",
) -> np.ndarray:
    g0, g1, g2 = _norm_gridsize(grid_size)
    j = np.tile(np.repeat(np.linspace(*lightness_bounds, g0), g2), g1)
    c = np.repeat(np.linspace(*chroma_bounds, g1), g0 * g2)
    h = np.tile(np.linspace(*hue_bounds, g2), g0 * g1)
    colors = np.vstack([j, c, h]).T

    if output_colorspace != "JCh":
        # Drop unrepresentable colors
        colors = _cspace_convert(colors, "JCh", "sRGB1")
        colors = colors[np.all((colors >= 0.0) & (colors <= 1.0), axis=1)]
        # convert to output space
        colors = _cspace_convert(colors, "sRGB1", output_colorspace)
    return colors.astype(np.float32, order="C")


def constrain_by_lightness_chroma_hue(
    colors: np.ndarray,
    current_colorspace: str,
    output_colorspace: str = "CAM02-UCS",
    lightness_bounds: tuple[float, float] = (10, 90),
    chroma_bounds: tuple[float, float] = (10, 90),
    hue_bounds: tuple[float, float] = (0, 360),
) -> np.ndarray:
    """Constrain `colors` to fit with a given set of l, c, h bounds."""
    if current_colorspace != "JCh":
        colors = _cspace_convert(colors, current_colorspace, "JCh")

    mask = np.ones(colors.shape[0], dtype=np.bool_)
    c0 = colors[:, 0]
    c1 = colors[:, 1]
    c2 = colors[:, 2]

    mask &= (c0 >= lightness_bounds[0]) & (c0 <= lightness_bounds[1])
    mask &= (c1 >= chroma_bounds[0]) & (c1 <= chroma_bounds[1])
    if hue_bounds[0] > hue_bounds[1]:
        mask &= (c2 >= hue_bounds[0]) | (c2 <= hue_bounds[1])
    else:
        mask &= (c2 >= hue_bounds[0]) & (c2 <= hue_bounds[1])

    colors = np.ascontiguousarray(colors[mask])

    if output_colorspace != "JCh":
        colors = _cspace_convert(colors, "JCh", output_colorspace)

    return colors.astype(np.float32, order="C")
