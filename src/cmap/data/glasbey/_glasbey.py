# glasbey vendored from https://github.com/lmcinnes/glasbey.
# see __init__ and LICENSE_GLASBEY
from __future__ import annotations

from typing import Literal, cast

import numpy as np

from ._grids import (
    _cspace_convert,
    constrain_by_lightness_chroma_hue,
    jch_grid,
    rgb_grid,
)

WB = np.array([[1.0, 1.0, 1.0], [0.0, 0.0, 0.0]])


def create_palette(
    palette_size: int = 256,
    *,
    grid_size: int | tuple[int, int, int] = 64,
    grid_space: Literal["RGB", "JCh"] = "RGB",
    lightness_bounds: tuple[float, float] = (10, 90),
    chroma_bounds: tuple[float, float] = (10, 90),
    hue_bounds: tuple[float, float] = (0, 360),
    red_bounds: tuple[float, float] = (0, 1),
    green_bounds: tuple[float, float] = (0, 1),
    blue_bounds: tuple[float, float] = (0, 1),
    cvd_type: Literal["protanomaly", "deuteranomaly", "tritanomaly"] = "deuteranomaly",
    cvd_severity: float | None = None,
) -> list[str] | np.ndarray:
    """Create glasbey palette.

    Create a categorical color palette with ``palette_size`` many colours using the
    Glasbey algorithm with the given bounds on hue, chroma and lightness. This should
    generate a palette that maximizes the perceptual distances between colours in the
    palette up to the constraints on hue, chroma and lightness, and the granularity of
    the possible colour sampling grid.

    Parameters
    ----------
    palette_size: int (default 256)
        The number of colors the created palette should have.
    grid_size: int or triple of int (default 64)
        When generating a grid of colors that can be used for the platte this determines
        the size of the grid. If a single int is given this determines the side length
        of the cube sampling the grid color space. A grid_size of 256 in RGB will
        generate all colors that can be represented in RGB. If a triple of ints is given
        then it is the side lengths of cuboid sampling the grid color space. This can be
        useful if sampling JCH space when you may want to sample more hues than chroma
        values, for example.
    grid_space: "RGB" or "JCh" (default RGB)
        The color space to sample the grid from. Sampling RGB space is the best option
        to ensure representable colors, however it can be useful to sample JCh
        (lightness, chroma, hue) space instead if you want to use a smaller grid size,
        but what to maintain sampling density with respect to lightness, chroma or hue
        constraints.
    lightness_bounds: (float, float) (default (10, 90))
        The upper and lower bounds of lightness values for the colors to be used in the
        resulting palette.
    chroma_bounds: (float, float) (default (10, 90))
        The upper and lower bounds of chroma values for the colors to be used in the
        resulting palette.
    hue_bounds: (float, float) (default (0, 360))
        The upper and lower bounds of hue values for the colors to be used in the
        resulting palette.
    red_bounds: (float, float) (default (0.0, 1.0))
        The upper and lower bounds of red channel values for the colors to be used in
        the resulting palette if sampling the grid from RGB space.
    green_bounds: (float, float) (default (0.0, 1.0))
        The upper and lower bounds of green channel values for the colors to be used in
        the resulting palette if sampling the grid from RGB space.
    blue_bounds: (float, float) (default (0.0, 1.0))
        The upper and lower bounds of blue channel values for the colors to be used in
        the resulting palette if sampling the grid from RGB space.
    colorblind_safe: bool (default False)
        If True the created palette will attempt to select colours in a way that should
        be more easily distinguishable for individuals with color vision deficiency. In
        particular the palette will be selected using distance in CAM02-UCS space of a
        color vision deficient simulation of the sampling grid, so distances will more
        closely resemble perceptual distances of individuals with color vision
        deficiency.
    cvd_type: Literal["protanomaly", "deuteranomaly", "tritanomaly"]
        The type of colour vision deficiency to attempt to be robust to if
        ``colorblind_safe`` is True. The cvd_type will be passed to colorspacious to
        simulate the appropriate colour vision deficiency. Per the colorspacious docs:
        * "protanomaly": A common form of red-green colorblindness; affects ~2% of white
          men to some degree (less common among other ethnicities, much less common
          among women).
        * "deuteranomaly": The most common form of red-green colorblindness; affects ~6%
          of white men to some degree (less common among other ethnicities, much less
          common among women).
        * "tritanomaly": A very rare form of colorblindness affecting blue/yellow
          discrimination - so rare that its detailed effects and even rate of occurrence
          are not well understood. Affects <0.1% of people, possibly much less. Also,
          the name we use here is somewhat misleading because only full tritanopia has
          been documented, and partial tritanomaly likely does not exist. What this
          means is that while Colorspacious will happily allow any severity value to be
          passed, probably only severity = 100 corresponds to any real people.
    cvd_severity: float between 0 and 100 (default 50.0)
        The severity of colour vision deficiency to attemnpt to be robust to if
        ``colorblind_safe`` is True. The cvd_severity will be passed to colorspacious to
        similate the appropriate colour vision deficiency. Per the colorspacious docs:
        Severity is any number between 0 (indicating regular vision) and 100 (indicating
        complete dichromacy).

    Returns
    -------
    palette: List of hex-code string or array of shape (palette_size, 3)
        The palette created, either as hex colors, or an array of floats of RGB values
        -- consumable by most plotting libraries.
    """
    try:
        import colorspacious  # noqa: F401
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "The colorspacious package is required to run glasbey.create_palette"
        ) from e

    if grid_space.lower() == "jch":
        colors = jch_grid(
            grid_size=grid_size,
            lightness_bounds=lightness_bounds,
            chroma_bounds=chroma_bounds,
            hue_bounds=hue_bounds,
            output_colorspace="CAM02-UCS",
        )
    elif grid_space.lower() == "rgb":
        colors = rgb_grid(
            grid_size=grid_size,
            red_bounds=red_bounds,
            green_bounds=green_bounds,
            blue_bounds=blue_bounds,
            output_colorspace="JCh",
        )
        colors = constrain_by_lightness_chroma_hue(
            colors,
            "JCh",
            lightness_bounds=lightness_bounds,
            chroma_bounds=chroma_bounds,
            hue_bounds=hue_bounds,
        )
    else:  # pragma: no cover
        raise ValueError(
            f'Parameter grid_space should be one of "JCh" or "RGB" not {grid_space!r}'
        )
    initial = _cspace_convert(WB, "sRGB1", "CAM02-UCS").astype(np.float32, order="C")

    if cvd_severity is None:
        from ._internals import generate_palette_cam02ucs  # type: ignore

        palette = generate_palette_cam02ucs(
            colors, initial, np.uint32(palette_size + 2)
        )
        return _get_rgb_palette(palette)[2:]

    if not isinstance(cvd_severity, float) and 0 <= cvd_severity <= 100:
        raise ValueError(  # pragma: no cover
            f"cvd_severity should be a float between 0 and 100 not {cvd_severity}"
        )

    from ._internals import generate_palette_cam02ucs_and_other  # type: ignore

    cvd_space = {
        "name": "sRGB1+CVD",
        "cvd_type": cvd_type,
        "severity": cvd_severity,
    }
    cvd_colors = _cspace_convert(colors, "CAM02-UCS", "sRGB1")
    cvd_colors = _cspace_convert(cvd_colors, cvd_space, "CAM02-UCS").astype(
        np.float32, order="C"
    )

    palette = generate_palette_cam02ucs_and_other(
        colors,
        cvd_colors,
        initial,
        initial,
        np.uint32(palette_size + 2),
        np.float32(0.0),
    )
    return _get_rgb_palette(palette)[2:]


def _get_rgb_palette(cam02ucs_palette: np.ndarray) -> np.ndarray:
    raw_rgb_palette = _cspace_convert(cam02ucs_palette, "CAM02-UCS", "sRGB1")
    out = np.clip(raw_rgb_palette, 0.0, 1.0)
    return cast("np.ndarray", out)
