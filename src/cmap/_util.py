from __future__ import annotations

import sys
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np

gradient = np.linspace(0, 1, 256)
gradient = np.vstack((gradient, gradient))

if TYPE_CHECKING:
    from collections.abc import Sequence

    import matplotlib.colors
    from matplotlib.figure import Figure as MplFigure
    from numpy.typing import ArrayLike, NDArray

    from cmap import Colormap

    from ._color import ColorLike
    from ._colormap import ColorStopsLike, Interpolation


def _ensure_cmap(cmap: Colormap | str) -> Colormap:
    from cmap import Colormap

    cm = Colormap(cmap) if isinstance(cmap, str) else cmap
    if not isinstance(cm, Colormap):  # pragma: no cover
        raise TypeError(f"Expected Colormap or str, got {type(cm)}")
    return cm


def plot_color_gradients(
    cmap_list: Sequence[str | Colormap], compare: bool = False
) -> MplFigure:
    # Create figure and adjust figure height to number of colormaps
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    nrows = len(cmap_list) * (2 if compare else 1)
    figh = 0.35 + 0.15 + (nrows + (nrows - 1) * 0.1) * 0.22
    fig, axs = plt.subplots(nrows=nrows + 1, figsize=(6.4, figh))
    bottom = 0.15 / figh
    top = 1 - 0.35 / figh
    if bottom >= top:  # pragma: no cover
        bottom, top = top, bottom
    fig.subplots_adjust(top=top, bottom=bottom, left=0.2, right=0.99)

    for i, (ax, name) in enumerate(zip(axs[:: 2 if compare else 1], cmap_list)):
        cm = _ensure_cmap(name).to_mpl()
        ax.imshow(gradient, aspect="auto", cmap=cm)
        ax.text(
            -0.01,
            0.5,
            name,
            va="center",
            ha="right",
            fontsize=10,
            transform=ax.transAxes,
        )
        if compare and name in mpl.colormaps:
            cm2 = mpl.colormaps[name]
            ax2 = axs[i * 2 + 1]
            ax2.imshow(gradient, aspect="auto", cmap=cm2)
            ax2.text(
                -0.01,
                0.5,
                "mpl",
                va="center",
                ha="right",
                fontsize=10,
                transform=ax2.transAxes,
            )

    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axs:
        ax.set_axis_off()
    return fig


def plot_rgb(cmap: Colormap | str, N: int = 256) -> MplFigure:
    """Plot the R,G,B,A components of a colormap individually."""
    import matplotlib.pyplot as plt

    x = np.linspace(0, 1, N)
    fig, ax = plt.subplots()
    colors = _ensure_cmap(cmap)(x, N=N)
    ax.plot(x, colors[:, 0], color="r", label="Red")
    ax.plot(x, colors[:, 1], color="g", label="Green")
    ax.plot(x, colors[:, 2], color="b", label="Blue")
    ax.plot(x, colors[:, 3], color="k", label="Alpha", linestyle="--", alpha=0.5)
    return fig


def calc_lightness(
    cmap: Colormap | str, x: ArrayLike | None = None, colorspace: str = "CAM02-UCS"
) -> np.ndarray:
    """Calculate the L* component of a colormap in CAM02-UCS over range 0-1.

    Parameters
    ----------
    cmap : Colormap
        The colormap to calculate lightness for.
    x : np.ndarray, optional
        The values to calculate lightness for, by default np.linspace(0.0, 1.0, 101)
    colorspace : str, optional
        The colorspace to calculate lightness in, by default "CAM02-UCS"
    """
    try:
        from colorspacious import cspace_converter
    except ImportError as e:
        raise ImportError(
            "This function requires the colorspacious package. "
            "Please `pip install colorspacious` and try again."
        ) from e

    x = np.linspace(0.0, 1.0, 101) if x is None else np.asarray(x)
    rgb = _ensure_cmap(cmap)(x, N=4000)[None, :, :3]
    lab = cspace_converter("sRGB1", colorspace)(rgb)
    return cast("np.ndarray", lab[0, :, 0])


def plot_lightness(
    cmap: Colormap | str,
    x: ArrayLike | None = None,
    colorspace: str = "CAM02-UCS",
    reverse: bool = False,
) -> MplFigure:
    """Plot L* component of a colormap in `colorspace` over range 0-1.

    see colorspacious docs for valid colorspace strings:
    https://colorspacious.readthedocs.io/en/latest/reference.html#supported-colorspaces

    Parameters
    ----------
    cmap : Colormap
        The colormap to calculate lightness for.
    x : np.ndarray, optional
        The values to calculate lightness for, by default np.linspace(0.0, 1.0, 101)
    colorspace : str, optional
        The colorspace to calculate lightness in, by default "CAM02-UCS"
    reverse : bool, optional
        Whether to reverse the colormap, by default False
    """
    import matplotlib.pyplot as plt

    x = np.linspace(0.0, 1.0, 101) if x is None else np.asarray(x)
    cmap = _ensure_cmap(cmap)
    lab = calc_lightness(cmap, x, colorspace)
    lslice = np.s_[::-1] if reverse else slice(None)
    y_ = lab[lslice]
    c_ = x[lslice]

    if hasattr(cmap, "to_mpl"):
        cmap = cmap.to_mpl()

    fig, ax = plt.subplots()
    ax.scatter(x, y_, c=c_, cmap=cmap, s=250, linewidths=0)
    ax.plot(x, y_, c="black", linewidth=1, alpha=0.2)
    ax.set_ylabel("Lightness $L^*$", fontsize=12)
    ax.set_xlabel("Value", fontsize=12)
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.2)
    return fig


# from matplotlib.colors
def hsv_to_rgb(hsv: ArrayLike) -> NDArray:
    """Convert hsv values to rgb.

    Parameters
    ----------
    hsv : (..., 3) array-like
       All values assumed to be in range [0, 1]

    Returns
    -------
    (..., 3) ndarray
       Colors converted to RGB values in range [0, 1]
    """
    hsv = np.asarray(hsv)

    # check length of the last dimension, should be _some_ sort of rgb
    if hsv.shape[-1] != 3:
        raise ValueError(
            f"Last dimension of input array must be 3; shape {hsv.shape} was found."
        )

    in_shape = hsv.shape
    hsv = np.array(
        hsv,
        copy=False,
        dtype=np.promote_types(hsv.dtype, np.float32),  # Don't work on ints.
        ndmin=2,  # In case input was 1D.
    )

    h = hsv[..., 0]
    s = hsv[..., 1]
    v = hsv[..., 2]

    r = np.empty_like(h)
    g = np.empty_like(h)
    b = np.empty_like(h)

    i = (h * 6.0).astype(int)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    idx = i % 6 == 0
    r[idx] = v[idx]
    g[idx] = t[idx]
    b[idx] = p[idx]

    idx = i == 1
    r[idx] = q[idx]
    g[idx] = v[idx]
    b[idx] = p[idx]

    idx = i == 2
    r[idx] = p[idx]
    g[idx] = v[idx]
    b[idx] = t[idx]

    idx = i == 3
    r[idx] = p[idx]
    g[idx] = q[idx]
    b[idx] = v[idx]

    idx = i == 4
    r[idx] = t[idx]
    g[idx] = p[idx]
    b[idx] = v[idx]

    idx = i == 5
    r[idx] = v[idx]
    g[idx] = p[idx]
    b[idx] = q[idx]

    idx = s == 0
    r[idx] = v[idx]
    g[idx] = v[idx]
    b[idx] = v[idx]

    rgb = np.stack([r, g, b], axis=-1)
    return cast("NDArray", rgb.reshape(in_shape))


def sineramp(
    shape: tuple[int, int] | int = (256, 512),
    amp: float = 0.05,
    wavelen: float = 8,
    power: float = 2,
) -> np.ndarray:
    """Generate test image consisting of a sine wave superimposed on a ramp function.

    This function and all documentation is based on the MATLAB function of the same
    name, written by Peter Kovesi and available from his website:
    https://www.peterkovesi.com/matlabfns/

    Copyright (c) 1996-2005 Peter Kovesi
    School of Computer Science & Software Engineering
    The University of Western Australia

    The test image consists of a sine wave superimposed on a ramp function The
    amplitude of the sine wave is modulated from its full value at the top of the
    image to 0 at the bottom.

    The image is useful for evaluating the effectiveness of different color maps.
    Ideally the sine wave pattern should be equally discernible over the full
    range of the color map.  In addition, across the bottom of the image, one
    should not see any identifiable features as the underlying signal is a smooth
    ramp.  In practice many color maps have uneven perceptual contrast over their
    range and often include 'flat spots' of no perceptual contrast that can hide
    significant features.

    Parameters
    ----------
    shape : tuple, optional
        [rows cols] specifying size of test image.  If a single value is supplied
        the image is square. Defaults to [256 512];  Note the number of columns is
        nominal and will be adjusted so that there are an integer number of sine wave
        cycles across the image.
    amp : float, optional
        Amplitude of sine wave. Defaults to 12.5
    wavelen : float, optional
        Wavelength of sine wave in pixels. Defaults to 8.
    power : float, optional
        Power to which the linear attenuation of amplitude, from top to bottom, is
        raised.  For no attenuation use p = 0.  For linear attenuation use a value
        of 1.  For contrast sensitivity experiments use larger values of p.  The
        default value is 2.

    Returns
    -------
    im : ndarray
        Test image
    """
    if isinstance(shape, int):
        rows = cols = shape
    elif len(shape) == 2:
        rows, cols = shape
    else:  # pragma: no cover
        raise ValueError("size must be a 1 or 2 element vector")

    # Adjust width of image so that we have an integer number of cycles of
    # the sinewave.  This is helps should one be using the test image to
    # evaluate a cyclic colour map.  However you will still see a slight
    # cyclic discontinuity at the top of the image, though this will
    # disappear at the bottom of the test image
    cycles = round(cols / wavelen)
    cols = int(cycles * wavelen)

    # Sine wave
    x = np.arange(cols)
    fx = amp * np.sin(1 / wavelen * 2 * np.pi * x)

    # Vertical modulating function
    A = (np.arange(rows - 1, -1, -1) / (rows - 1)) ** power
    im = A[:, np.newaxis] * fx

    # Add ramp
    ramp = np.arange(cols)[np.newaxis, :] / (cols - 1)
    im = im + ramp * (-2 * amp)

    # Now normalise each row so that it spans the full data range from 0 to 1.
    # This ensures that, at the lower edge of the image, the full colour map is
    # displayed.  It also helps with the evaluation of cyclic colour maps though
    # a small cyclic discontinuity will remain at the top of the test image.
    for r in range(rows):
        row_data = im[r, :]
        row_data -= row_data.min()
        row_data /= row_data.max()
        im[r, :] = row_data
    return cast("np.ndarray", im)


def circlesineramp(
    size: int = 512,
    amp: float = np.pi / 10,
    wavelen: float = 8,
    power: float = 2,
    hole: bool = True,
) -> np.ndarray:
    """Generate test image for evaluating cyclic color maps.

    This function and all documentation is based on the MATLAB function of the same
    name, written by Peter Kovesi and available from his website:
    https://www.peterkovesi.com/matlabfns/

    Copyright (c) 1996-2005 Peter Kovesi
    School of Computer Science & Software Engineering
    The University of Western Australia

    The test image is a circular pattern consistsing of a sine wave superimposed
    on a spiral ramp function.  The spiral ramp starts at a value of 0 pointing
    right, increasing anti-clockwise to a value of 2*pi as it completes the full
    circle. This gives a 2*pi discontinuity on the right side of the image.  The
    amplitude of the superimposed sine wave is modulated from its full value at
    the outside of the circular pattern to 0 at the centre.  The default sine wave
    amplitude of pi/10 means that the overall size of the sine wave from peak to
    trough represents 2*(pi/10)/(2*pi) = 10% of the total spiral ramp of 2*pi.  If
    you are testing your colour map over a cycle of pi you should use amp = pi/20
    to obtain an equivalent ratio of sine wave to circular ramp.

    The image is designed for evaluating the effectiveness of cyclic colour maps.
    It is the cyclic companion to `sineramp`.  Ideally the sine wave pattern should
    be equally discernible over all angles around the test image.  In practice
    many colourmaps have uneven perceptual contrast over their range and often
    include 'flat spots' of no perceptual contrast that can hide significant
    features (e.g. hsv colour map).

    Parameters
    ----------
    size : int, optional
        Size of one side of the test image.  Defaults to 512.
    amp : float, optional
        Amplitude of sine wave. Defaults to 12.5
    wavelen : float, optional
        Wavelength of sine wave in pixels. Defaults to 8.
    power : float, optional
        Power to which the linear attenuation of amplitude, from top to bottom, is
        raised.  For no attenuation use p = 0.  For linear attenuation use a value
        of 1.  For contrast sensitivity experiments use larger values of p.  The
        default value is 2.
    hole : bool, optional
        If True, the test image will have a hole in the centre.  Defaults to True.

    Returns
    -------
    np.ndarray
        Test image of size (size, size) with values in the range 0-2*pi.
    """
    # Set values for inner and outer radii of test pattern
    maxr = size / 2 * 0.9
    minr = 0.15 * size if hole else 0

    # Determine number of cycles to achieve desired wavelength at half radius
    meanr = (maxr + minr) / 2
    circum = 2 * np.pi * meanr
    cycles = round(circum / wavelen)

    # Angles are +ve anticlockwise and mod 2*pi
    indices = np.arange(0, size) - size / 2
    x, y = np.meshgrid(indices, indices)
    theta = np.mod(np.arctan2(-y, x), 2 * np.pi)
    rad = np.sqrt(x**2 + y**2)

    # Normalise radius so that it varies 0-1 over minr to maxr
    rad = (rad - minr) / (maxr - minr)

    # Form the image
    im = amp * rad**power * np.sin(cycles * theta) + theta

    # Ensure all values are within 0-2*pi so that a simple default display
    # with a cyclic colour map will render the image correctly.
    im = np.mod(im, 2 * np.pi)

    # 'Nanify' values outside normalised radius values of 0-1
    alpha = np.ones_like(im)
    im[rad > 1] = np.nan
    alpha[rad > 1] = 0

    if hole:
        im[rad < 0] = np.nan
        alpha[rad < 0] = 0

    return cast("np.ndarray", im * alpha)


class ReportDict(TypedDict):
    x: np.ndarray
    R: np.ndarray
    G: np.ndarray
    B: np.ndarray
    J: np.ndarray
    a: np.ndarray
    b: np.ndarray
    color: list[str]
    chroma: np.ndarray
    hue: np.ndarray
    colorfulness: np.ndarray
    saturation: np.ndarray
    perceptual_derivs: np.ndarray
    lightness_derivs: np.ndarray


class CVDReportDict(TypedDict):
    normal: ReportDict
    protan: ReportDict
    deutan: ReportDict
    tritan: ReportDict


def report(
    cm: Colormap,
    n: int = 256,
    uniform_space: str = "CAM02-UCS",
    initial_space: dict = {"name":"sRGB1"}
) -> ReportDict:
    """Generate a report of data describing a colormap.

    This is primarily used for generating charts in the documentation
    """
    from colorspacious import cspace_convert

    if len(cm.color_stops) >= 100:
        RGBA = np.asarray(cm.color_stops.color_array)
        n = RGBA.shape[0]
        x = np.linspace(0, 1, n)
    else:
        x = np.linspace(0, 1, n)
        RGBA = cm(x)
    RGB = RGBA[:, :3]

    RGB = np.clip(cast("np.ndarray", cspace_convert(RGB, initial_space, "sRGB1")), 0, 1)
    Jab = cast("np.ndarray", cspace_convert(RGB, "sRGB1", uniform_space))

    local_deltas = np.sqrt(np.sum((Jab[:-1, :] - Jab[1:, :]) ** 2, axis=-1))
    local_deltas = np.insert(local_deltas, 0, 0)  # keep length the same
    percep_derivs = n * local_deltas  # export

    lightness_deltas = np.diff(Jab[:, 0])
    lightness_deltas = np.insert(lightness_deltas, 0, 0)  # keep length same
    lightness_derivs = n * lightness_deltas  # export

    JchMs = cspace_convert(RGB, "sRGB1", "JChMs")
    color = [
        f"#{r:02X}{g:02X}{b:02X}"
        for r, g, b in np.clip(RGB * 255, 0, 255).astype("uint8")
    ]

    return {
        "x": x,
        "R": RGB[:, 0],
        "G": RGB[:, 1],
        "B": RGB[:, 2],
        "J": Jab[:, 0],
        "a": Jab[:, 1],
        "b": Jab[:, 2],
        "color": color,
        "chroma": JchMs[:, 1],
        "hue": JchMs[:, 2],
        "colorfulness": JchMs[:, 3],
        "saturation": JchMs[:, 4],
        "perceptual_derivs": percep_derivs,
        "lightness_derivs": lightness_derivs,
    }

    # J -> lightness
    # C -> chroma
    # h -> hue angle
    # Q -> brightness
    # M -> colorfulness
    # s -> saturation
    # H -> hue composition


def report_cvds(
    cm: Colormap, n: int = 256, uniform_space: str = "CAM02-UCS"
) -> CVDReportDict:
    """Generate a report of data describing a colormap for different CVD types.

    This is primarily used for generating charts in the documentation
    """
    return {
        "normal": report(cm, n=n, uniform_space=uniform_space),
        "protan": report(
            cm,
            n=n,
            uniform_space=uniform_space,
            initial_space={
                "name": "sRGB1+CVD",
                "cvd_type": "protanomaly",
                "severity": 100,
            },
        ),
        "deutan": report(
            cm,
            n=n,
            uniform_space=uniform_space,
            initial_space={
                "name": "sRGB1+CVD",
                "cvd_type": "deuteranomaly",
                "severity": 100,
            },
        ),
        "tritan": report(
            cm,
            n=n,
            uniform_space=uniform_space,
            initial_space={
                "name": "sRGB1+CVD",
                "cvd_type": "tritanomaly",
                "severity": 100,
            },
        ),
    }


def to_mpl(
    value: ColorStopsLike,
    /,
    *,
    name: str | None = None,
    identifier: str | None = None,
    category: str | None = None,
    interpolation: Interpolation | bool | None = None,
    under: ColorLike | None = None,
    over: ColorLike | None = None,
    bad: ColorLike | None = None,
    N: int = 256,
    gamma: float = 1.0,
) -> matplotlib.colors.Colormap:
    """Convienence function to create a matplotlib colormap.

    Arguments are the same as for [cmap.Colormap][]. This simply creates the
    colormap instance and returns the value of `to_matplotlib()`.
    """
    from cmap import Colormap

    cm = Colormap(
        value,
        name=name,
        identifier=identifier,
        category=category,
        interpolation=interpolation,
        under=under,
        over=over,
        bad=bad,
    )
    return cm.to_matplotlib(N=N, gamma=gamma)


if __name__ == "__main__":  # pragma: no cover
    import matplotlib.pyplot as plt

    plot_color_gradients(sys.argv[1:], compare=True)
    plot_lightness(sys.argv[1])
    plt.show()
