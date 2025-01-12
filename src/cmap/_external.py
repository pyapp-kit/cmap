"""Functions for interacting with external libraries."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pygfx
    from bokeh.models import LinearColorMapper as BokehLinearColorMapper
    from matplotlib.colors import Colormap as MplColormap
    from matplotlib.colors import LinearSegmentedColormap as MplLinearSegmentedColormap
    from matplotlib.colors import ListedColormap as MplListedColormap
    from matplotlib.figure import Figure as MplFigure
    from napari.utils.colormaps import Colormap as NapariColormap
    from pyqtgraph import ColorMap as PyqtgraphColorMap
    from vispy.color import Colormap as VispyColormap

    from ._color import Color
    from ._colormap import Colormap


def to_mpl(
    cm: Colormap, N: int = 256, gamma: float = 1.0
) -> MplLinearSegmentedColormap | MplListedColormap:
    """Return a matplotlib colormap."""
    import matplotlib.colors as mplc

    mpl_cm: mplc.Colormap
    if cm.interpolation == "nearest":
        mpl_cm = mplc.ListedColormap(colors=cm.color_stops.color_array, name=cm.name)
    else:
        try:
            mpl_cm = mplc.LinearSegmentedColormap.from_list(
                cm.name, cm.color_stops, N=N, gamma=gamma
            )
        except ValueError as e:  # pragma: no cover
            from matplotlib import __version__

            # broken in matplotlib 3.8.0, fixed by
            # https://github.com/matplotlib/matplotlib/pull/26952
            if len(cm.color_stops) == 2 and __version__ == "3.8.0":
                raise ValueError(
                    "matplotlib 3.8.0 has a bug that prevents creating a colormap "
                    "from only two colors.  Please upgrade or downgrade matplotlib."
                ) from e
            raise

    return mpl_cm.with_extremes(
        bad=cm.bad_color,
        over=cm.over_color,
        under=cm.under_color,
    )


def to_vispy(cm: Colormap) -> VispyColormap:
    """Return a vispy colormap."""
    from vispy.color import Colormap

    return Colormap(colors=cm.color_stops.color_array, controls=cm.color_stops.stops)


def to_pygfx(cm: Colormap, N: int = 256) -> pygfx.Texture:
    """Return a pygfx Texture."""
    import pygfx

    # TODO: check whether pygfx has it's own stop-aware interpolation,
    # and if so, use that instead of .lut()
    # (get_view has a filter argument... but I don't know whether it will take
    # care of the stops)
    return pygfx.Texture(cm.lut(N).astype(np.float32), dim=1)


def to_plotly(cm: Colormap) -> list[list[float | str]]:
    """Return a plotly colorscale."""
    return [[pos, color.rgba_string] for pos, color in cm.color_stops]


def to_napari(cm: Colormap) -> NapariColormap:
    """Return a napari colormap."""
    from napari.utils.colormaps import Colormap

    return Colormap(
        colors=cm.color_stops.color_array,
        controls=cm.color_stops.stops,
        name=cm.identifier or "custom colormap",
        display_name=cm.name,
    )


def to_bokeh(cm: Colormap, N: int = 256) -> BokehLinearColorMapper:
    """Return a bokeh colorscale, with N color samples from the colormap."""
    from bokeh.models import LinearColorMapper

    # TODO: check whether bokeh has it's own interpolation, and if so, use that
    return LinearColorMapper([color.hex for color in cm.iter_colors(N)])


def to_altair(cm: Colormap, N: int = 256) -> list[str]:
    """Return an altair colorscale with N color samples from the colormap.

    Suitable for passing to the range parameter of altair.Scale.
    """
    return [color.hex for color in cm.iter_colors(N)]


def to_gee(cm: Colormap, N: int = 256) -> list[str]:
    """Return a Google Earth Engine palette with N color samples from the colormap.

    Suitable for passing to the palette parameter of Google Earth Engine visualizations.

    See details at
    https://developers.google.com/earth-engine/guides/image_visualization#color-palettes
    """
    rgbs = [
        # drop the # symbol
        color.hex.lstrip("#")
        for color in cm.iter_colors(N)
    ]
    return rgbs


def to_pyqtgraph(cm: Colormap) -> PyqtgraphColorMap:
    """Return a `pyqtgraph.Colormap`."""
    from pyqtgraph import ColorMap

    colors = (cm.color_stops.color_array * 255).astype(np.uint8)
    return ColorMap(cm.color_stops.stops, colors, name=cm.name)


# ==========================================


def viscm_plot(
    cmap: Colormap | MplColormap, dpi: int = 100, dest: str | None = None
) -> MplFigure:
    """Evaluate goodness of colormap using perceptual deltas.

    Parameters
    ----------
    cmap : Colormap
        Colormap instance.
    dpi : int, optional
        dpi for saved image. Defaults to 100.
    dest : str, optional
        If provided, the image will be saved to this path. Defaults to None.

    """
    try:
        # XXX: this is to avoid an import provlem in viscm, until the fix is released
        # https://github.com/matplotlib/viscm/issues/61
        import matplotlib.backends.backend_qt4agg  # noqa: F401
    except ImportError:
        import sys
        from unittest.mock import MagicMock

        sys.modules["matplotlib.backends.backend_qt4agg"] = MagicMock()

    try:
        import matplotlib.pyplot as plt
        from viscm import viscm
    except ModuleNotFoundError as e:  # pragma: no cover
        raise type(e)(
            "viscm is required to use this method. Please `pip install viscm`."
        ) from e

    if hasattr(cmap, "to_mpl"):
        cmap = cmap.to_mpl()

    viscm(cmap)
    fig = plt.gcf()
    fig.set_size_inches(16, 8)
    with contextlib.suppress(AttributeError):
        fig.canvas.manager.set_window_title(cmap.name)

    if dest:
        fig.savefig(dest, bbox_inches="tight", dpi=dpi)
    else:
        plt.show()  # pragma: no cover
    return fig


def rich_print_color(color: Color) -> None:
    """Print a rich Text object with the color as background color."""
    import rich
    from rich.style import Style
    from rich.text import Text

    # TODO: this is a side-effect
    # it "works" to print a small color patch if rich is used,
    # but it would be better to yield something that rich can actually render.
    console = rich.get_console()
    color_cell = Text("  ", style=Style(bgcolor=color.hex[:7]))
    console.print(color_cell, end="")


def rich_print_colormap(cm: Colormap, width: int | None = None) -> None:
    """Print a rich Text object with the colormap as background color."""
    from rich import get_console
    from rich.style import Style
    from rich.text import Text

    # TODO: this is a side-effect
    console = get_console()
    color_cell = Text("")
    # if cm.interpolation == "nearest":
    # width = len(cm.color_stops)
    width = width or (console.width - 12)
    for color in cm.iter_colors(width):
        color_cell += Text(" ", style=Style(bgcolor=color.hex[:7]))
    console.print(color_cell)
