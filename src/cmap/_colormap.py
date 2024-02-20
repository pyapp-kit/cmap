from __future__ import annotations

import base64
import warnings
from functools import partial
from numbers import Number
from typing import TYPE_CHECKING, Any, NamedTuple, Sequence, cast, overload

import numpy as np
import numpy.typing as npt

from . import _external
from ._catalog import Catalog
from ._color import Color

if TYPE_CHECKING:
    from typing import Callable, Iterable, Iterator, Literal, Union

    import bokeh.models
    import matplotlib.colors
    import matplotlib.figure
    import napari.utils.colormaps
    import pygfx
    import vispy.color
    from numpy.typing import ArrayLike, NDArray
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema
    from typing_extensions import TypeAlias, TypedDict, TypeGuard

    from ._catalog import CatalogItem
    from ._color import ColorLike

    Interpolation = Literal["linear", "nearest"]
    LutCallable: TypeAlias = Callable[[NDArray], NDArray]
    ColorStopLike: TypeAlias = Union[tuple[float, ColorLike], np.ndarray]
    # All of the things that we can pass to the constructor of Colormap
    ColorStopsLike: TypeAlias = Union[
        str,  # colormap name, w/ optional "_r" suffix
        Iterable[ColorLike | ColorStopLike],
        np.ndarray,
        "MPLSegmentData",
        dict[float, ColorLike],
        "ColorStops",
        LutCallable,
    ]

    class MPLSegmentData(TypedDict, total=False):
        red: list[tuple[float, float, float]] | Callable[[np.ndarray], np.ndarray]
        green: list[tuple[float, float, float]] | Callable[[np.ndarray], np.ndarray]
        blue: list[tuple[float, float, float]] | Callable[[np.ndarray], np.ndarray]
        alpha: list[tuple[float, float, float]] | Callable[[np.ndarray], np.ndarray]

    class ColormapDict(TypedDict):
        name: str
        identifier: str
        category: str | None
        value: list[tuple[float, list[float]]]


class Colormap:
    """A colormap is a mapping from scalar values to RGB(A) colors.

    Parameters
    ----------
    value : Color | ColorStop | Iterable[Color | ColorStop] | dict[float, Color]
        The color data to use for the colormap. Can be a single color, a single
        color stop, a sequence of colors and/or color stops, or a dictionary
        mapping scalar values to colors.

        Any of the following are valid:

        - a `str` containing a recognized string colormap name (e.g. `"viridis"`,
          `"magma"`), optionally suffixed with `"_r"` to reverse the colormap
          (e.g. `"viridis"`, `"magma_r"`).
        - An iterable of [ColorLike](/colors#colorlike-objects) values (any object that
          can be cast to a [`Color`][cmap.Color]), or "color-stop-like" tuples (
          `(float, ColorLike)` where the first element is a scalar value specifying the
          position of the color in the gradient. When using color stops, the stop
          position values should be in the range [0, 1]. If no scalar stop positions are
          given, they will be linearly interpolated between any neighboring stops (or
          0-1 if there are no stops).
        - a `dict` mapping scalar values to color-like values: e.g.
          `{0.0: "red", 0.5: (0, 1, 0), 1.0: "#0000FF"}`.
        - a matplotlib-style [segmentdata
          `dict`](https://matplotlib.org/stable/tutorials/colors/colormap-manipulation.html),
          with keys `"red"`, `"green"`, and `"blue"`, each of which maps to a list of
          tuples of the form `(x, y0, y1)`, or a callable that takes an array of values
          in the range [0, 1] and returns an array of values in the range [0, 1].  See
          the matplotlib docs for more.
        - a `Callable` that takes an array of N values in the range [0, 1] and returns
          an (N, 4) array of RGBA values in the range [0, 1].
    name : str | None
        A name for the colormap. If None, will be set to the identifier or the string
        `"custom colormap"`.
    identifier : str | None
        The identifier of the colormap. If None, will be set to the name, converted
        to lowercase and with spaces and dashes replaced by underscores.
    category : str | None
        An optional category of the colormap (e.g. `"diverging"`, `"sequential"`).
        Not used internally.
    """

    __slots__ = (
        "color_stops",
        "name",
        "identifier",
        "category",
        "info",
        "_lut_cache",
        "interpolation",
        "_initialized",
        "__weakref__",
    )

    #: ColorStops dett
    color_stops: ColorStops

    name: str
    identifier: str
    category: str | None
    interpolation: Interpolation
    info: CatalogItem | None

    _catalog_instance: Catalog | None = None

    @classmethod
    def catalog(cls) -> Catalog:
        """Return the global colormaps catalog."""
        if cls._catalog_instance is None:
            cls._catalog_instance = Catalog()
        return cls._catalog_instance

    def __init__(
        self,
        value: ColorStopsLike,
        *,
        name: str | None = None,
        identifier: str | None = None,
        category: str | None = None,
        interpolation: Interpolation | bool | None = None,
    ) -> None:
        if isinstance(value, str):
            rev = value.endswith("_r")
            info = self.catalog()[value[:-2] if rev else value]
            name = name or f"{info.namespace}:{info.name}"
            category = category or info.category
            self.info = info
            if isinstance(info.data, list):
                ld = len(info.data[0])
                if ld == 2:
                    # if it's a list of tuples, it's a list of color stops
                    stops = ColorStops._from_uniform_stops(info.data)
                elif ld == 3:
                    stops = ColorStops._from_colorarray_like(info.data)
                else:  # pragma: no cover
                    raise ValueError(
                        f"Invalid catalog colormap data for {info.name!r}: {info.data}"
                    )
            else:
                stops = _parse_colorstops(info.data)
            stops._interpolation = _norm_interp(interpolation or info.interpolation)
            interpolation = stops._interpolation
            if rev:
                stops = stops.reversed()
        elif isinstance(value, Colormap):
            name = name or value.name
            identifier = identifier or value.identifier
            self.info = value.info
            category = category or value.category
            interpolation = interpolation or value.interpolation
            stops = value.color_stops
            self.info = None
        else:
            stops = _parse_colorstops(value)
            self.info = None

        name = name or identifier
        if not name:
            name = value if isinstance(value, str) else "custom colormap"

        self.color_stops = stops
        self.name = name
        self.identifier = _make_identifier(identifier or name)
        self.category = category
        # TODO: this just clobbers the interpolation from the user...
        # need to unify with the catalog
        self.interpolation = _norm_interp(interpolation)

        self._lut_cache: dict[tuple[int, float], np.ndarray] = {}
        self._initialized = True

    @overload
    def __call__(
        # would prefer to make this Arraylike, but that overlaps with float
        self,
        x: NDArray | Sequence[float],
        *,
        N: int = 256,
        gamma: float = 1,
        bytes: bool = False,
    ) -> NDArray[np.float64]: ...

    @overload
    def __call__(
        self, x: float, *, N: int = 256, gamma: float = 1, bytes: bool = False
    ) -> Color: ...

    def __call__(
        self,
        x: float | NDArray | Sequence[float],
        *,
        N: int = 256,
        gamma: float = 1,
        bytes: bool = False,
    ) -> Color | NDArray[np.float64]:
        r"""Map scalar values in X to an RGBA array.

        This is the primary API for "using" a `cmap.Colormap` to map scalar values to
        colors.

        The dtype of x matters.  If x is an integer dtype, then it is interpreted as
        (fancy) indexing directly into the LUT.  If x is a float, then it is assumed to
        be a normalized value in [0, 1] and will be mapped linearly to the nearest color
        in the LUT (use a higher N for finer sampling).

        Parameters
        ----------
        x : float | array-like
            The scalar values to map to colors. If `x` is a float, a single color object
            will be returned. If x is an array-like, an array of RGBA colors will be
            returned with shape `x.shape + (4,)`.  See note above about the dtype of x.
        N : int
            Number of samples in the LUT. This is used to determine the resolution of
            the mapping (by default, 256).  Note that depending on the data being
            mapped, N can cause slight rounding errors in some cases.
            N of 256 is the default in matplotlib, so it is here as well, but note that
            N=255 (odd numbered) will result in an exact color match being returned for
            a value of 0.5 in a colormap with an odd number of colors.
        gamma : float
            The gamma value to use when creating the LUT.
        bytes : bool
            If False (default), the returned RGBA values will be floats in the
            interval ``[0, 1]`` otherwise they will be `numpy.uint8`\s in the
            interval ``[0, 255]``.

        Returns
        -------
        color : Color | NDArray
            If X is a float, a single RGBA color will be returned. If x is an
            array-like, an array of RGBA colors will be returned with shape
            `x.shape + (4,)`


        Examples
        --------
        >>> from cmap import Colormap
        >>> from tifffile import imread
        >>> cmap = Colormap("viridis")
        >>> data = imread('some_path.tif')
        >>> data = data - data.min()  # normalize to 0-1
        >>> data = data / data.max()  # normalize to 0-1
        >>> colored_img = cmap(data)
        """
        lut = self.lut(N=N, gamma=gamma)
        if bytes:
            lut = (lut * 255).astype(np.uint8)

        xa = np.array(x, copy=True)
        if not xa.dtype.isnative:
            xa = xa.byteswap().newbyteorder()  # Native byteorder is faster.
        if xa.dtype.kind == "f":
            N = len(lut)
            with np.errstate(invalid="ignore"):
                xa *= N
                # Negative values are out of range, but astype(int) would
                # truncate them towards zero.
                xa[xa < 0] = -1
                # xa == 1 (== N after multiplication) is not out of range.
                xa[xa == N] = N - 1
                # Avoid converting large positive values to negative integers.
                np.clip(xa, -1, N, out=xa)
                xa = xa.astype(int)

        result = lut.take(xa, axis=0, mode="clip")
        return result if np.iterable(x) else Color(result)

    def as_dict(self) -> ColormapDict:
        """Return a dictionary representation of the colormap.

        The returned dictionary is suitable for serialization, or for passing to the
        Colormap constructor.
        """
        return {
            "name": self.name,
            "identifier": self.identifier,
            "category": self.category,
            "value": [(p, list(c)) for p, c in self.color_stops],
        }

    def lut(self, N: int = 256, gamma: float = 1) -> np.ndarray:
        """Return a lookup table (LUT) for the colormap.

        The returned LUT is a numpy array of RGBA values, with shape (N, 4), where N is
        the number of requested colors in the LUT. The LUT can be used to map scalar
        values (that have been normalized to 0-1) to colors.

        The output of this function is used by the `__call__` method, but may also
        be used directly by users.

        LUTs of a particular size and gamma value are cached.

        Parameters
        ----------
        N : int
            The number of colors in the LUT.
        gamma : float
            The gamma value to use for the LUT.
        """
        if (N, gamma) not in self._lut_cache:
            self._lut_cache[(N, gamma)] = self.color_stops.to_lut(N, gamma)
        return self._lut_cache[(N, gamma)]

    def iter_colors(self, N: Iterable[float] | int | None = None) -> Iterator[Color]:
        """Return a list of N color objects sampled evenly over the range of the LUT.

        If N is an integer, it will return a list of N colors spanning the full range
        of the colormap. If N is an iterable, it will return a list of colors at the
        positions specified by the iterable.

        Parameters
        ----------
        N : int | Iterable[float] | None
            The number of colors to return, or an iterable of positions to sample. If
            not provided (the default), N will be set to the number of colors in the
            colormap.

        Yields
        ------
        color: Color
            Color objects.
        """
        if N is None:
            N = len(self.color_stops)
        nums = np.linspace(0, 1, N) if isinstance(N, int) else np.asarray(N)
        for c in self(nums, N=len(nums)):
            yield Color(c)

    def reversed(self, name: str | None = None) -> Colormap:
        """Return a new Colormap, with reversed colors.

        Parameters
        ----------
        name: str | None
            By default, the name of the new colormap will be the name of the original
            colormap with "_r" appended. If the original colormap name ends in "_r", the
            new colormap name will be the original name with "_r" removed. If the name
            argument is provided, it will be used as the name of the new colormap.
        """
        if name is None:
            name = self.name[:-2] if self.name.endswith("_r") else f"{self.name}_r"

        return type(self)(
            self.color_stops.reversed(), name=name, category=self.category
        )

    def to_css(
        self,
        max_stops: int | None = None,
        angle: int = 90,
        radial: bool = False,
        as_hex: bool = False,
    ) -> str:
        """Return a CSS representation of the colormap as a linear or radial gradient.

        Parameters
        ----------
        max_stops : int, optional
            May be used to limit the number of color stops in the css.
        angle : int, optional
            Angle of the gradient in degrees. by default 90. (ignored for radial)
        radial : bool, optional
            If `True`, return a radial gradient, by default False.
        as_hex : bool, optional
            If `True`, return colors as hex strings, by default use `rgba()` strings.

        Examples
        --------
        >>> from cmap import Colormap
        >>> print(Colormap("brg").to_css())
        background: rgb(0, 0, 255);
        background: linear-gradient(
            90deg, rgb(0, 0, 255) 0%, rgb(255, 0, 0) 50%, rgb(0, 255, 0) 100%
        );
        """
        return self.color_stops.to_css(
            max_stops=max_stops, angle=angle, radial=radial, as_hex=as_hex
        )

    def __setattr__(self, _name: str, _value: Any) -> None:
        if getattr(self, "_initialized", False):
            raise AttributeError("Colormap is immutable")
        object.__setattr__(self, _name, _value)

    def __reduce__(self) -> str | tuple[Any, ...]:
        # for pickle
        return self.__class__, (self.color_stops,)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Colormap):
            try:
                other = Colormap(other)  # type: ignore
            except Exception:
                return NotImplemented
        return self.color_stops == other.color_stops

    def __repr__(self) -> str:
        return f"Colormap(name={self.name!r}, <{len(self.color_stops)} colors>)"

    def _repr_png_(
        self, *, width: int = 512, height: int = 48, img: np.ndarray | None = None
    ) -> bytes:
        """Generate a PNG representation of the Colormap."""
        from ._png import encode_png

        X = img if img is not None else np.tile(np.linspace(0, 1, width), (height, 1))
        return encode_png(self(X, bytes=True))

    def _repr_html_(self) -> str:
        """Generate an HTML representation of the Colormap."""
        png_base64 = base64.b64encode(self._repr_png_()).decode("ascii")

        return (
            f'<div style="vertical-align: middle;"><strong>{self.name}</strong></div>'
            "<div>"
            f'<img alt="{self.name} colormap" title="{self.name}" '
            f'style="border: 1px solid #555;" src="data:image/png;base64,{png_base64}">'
            "</div>"
        )

    # -------------------------- RICH REPR SUPPORT ----------------------------------

    def __rich_repr__(self) -> Any:
        return _external.rich_print_colormap(self)  # side effect

    # -------------------------- PYDANTIC SUPPORT -----------------------------------

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from pydantic_core import core_schema

        schema = handler(Any)
        ser = core_schema.plain_serializer_function_ser_schema(lambda x: x.as_dict())
        return core_schema.no_info_after_validator_function(
            cls._validate, schema, serialization=ser
        )

    @classmethod
    def __get_validators__(cls) -> Iterator[Callable]:
        yield cls._validate  # pydantic validator

    @classmethod
    def _validate(cls, v: Any) -> Colormap:
        if isinstance(v, cls):
            return v  # pragma: no cover
        return cls(**v) if isinstance(v, dict) else cls(v)

    # pysgnal.EventedModel support
    def _json_encode(self) -> ColormapDict:
        return self.as_dict()

    # ------------------------- THIRD PARTY SUPPORT ---------------------------------

    def to_matplotlib(
        self, N: int = 256, gamma: float = 1.0
    ) -> matplotlib.colors.Colormap:
        """Return a matplotlib colormap."""
        return _external.to_mpl(self, N=N, gamma=gamma)

    to_mpl = to_matplotlib  # alias

    def to_vispy(self) -> vispy.color.Colormap:
        """Return a vispy colormap."""
        return _external.to_vispy(self)

    def to_pygfx(self, N: int = 256, *, as_view: bool | None = None) -> pygfx.Texture:
        """Return a pygfx Texture."""
        if as_view is not None:
            warnings.warn(
                "as_view argument is deprecated and does nothing",
                DeprecationWarning,
                stacklevel=2,
            )
        return _external.to_pygfx(self, N=N)

    def to_napari(self) -> napari.utils.colormaps.Colormap:
        """Return a napari colormap.

        https://napari.org/stable/api/napari.utils.Colormap.html
        """
        return _external.to_napari(self)

    def to_plotly(self) -> list[list[float | str]]:
        """Return a plotly colorscale."""
        return _external.to_plotly(self)

    def to_bokeh(self, N: int = 256) -> bokeh.models.LinearColorMapper:
        """Return a bokeh colorscale, with N color samples from the colormap.

        https://docs.bokeh.org/en/latest/docs/reference/models/mappers.html

        Parameters
        ----------
        N : int, optional
            Number of colors to sample from the colormap, by default 256.
        """
        return _external.to_bokeh(self, N=N)

    def to_altair(self, N: int = 256) -> list[str]:
        """Return an altair colorscale with N color samples from the colormap.

        Suitable for passing to the range parameter of altair.Scale.
        https://altair-viz.github.io/user_guide/customization.html#color-domain-and-range
        """
        return _external.to_altair(self, N=N)

    def to_viscm(
        self, dpi: int = 100, dest: str | None = None
    ) -> matplotlib.figure.Figure:
        """Plot colormap using viscm.  (Requires viscm to be installed.).

        See <https://github.com/matplotlib/viscm> for details

        Parameters
        ----------
        dpi : int, optional
            dpi for saved image. Defaults to 100.
        dest : str, optional
            If provided, the image will be saved to this path. Defaults to None.

        Returns
        -------
        fig : matplotlib.figure.Figure
            The figure object containing the plot.
        """
        return _external.viscm_plot(self, dpi, dest)


class ColorStop(NamedTuple):
    """A color stop in a color gradient."""

    position: float
    color: Color


def _norm_interp(interp: Interpolation | bool | str | None) -> Interpolation:
    if isinstance(interp, bool):
        return "linear" if interp else "nearest"
    elif not interp:
        return "linear"
    if interp not in {"linear", "nearest"}:
        raise ValueError(
            f"Invalid interpolation mode: {interp!r}. "
            "Must be one of 'linear' or 'nearest'"
        )
    return cast("Interpolation", interp)


class ColorStops(Sequence[ColorStop]):
    """A sequence of color stops in a color gradient.

    Convenience class allowing various operations on a sequence of color stops,
    including casting to an (N, 5) array (e.g. `np.asarray(ColorStops(...))`)

    This is the main internal representation of a colormap, and is used to construct
    the LUT used in the Colormap.__call__ method.

    Parameters
    ----------
    stops : array-like, optional
        An array of color stops, by default None (must provide either stops or lut_func)
        The array must be an (N, 5) array, where the first column is the position
        (0-1) and the remaining columns are the color (RGBA, 0-1).
    lut_func : callable, optional
        A callable that takes a single argument (an (N, 1) array of positions) and
        returns an (N, 4) array of colors.  This will be used to generate the LUT
        instead of the stops array.  If provided, the stops argument will be ignored.
    interpolation : str, optional
        Interpolation mode.  Must be one of 'linear' (or `True`) or 'nearest' (or
        `False`). Defaults to 'linear'.
    """

    _stops: np.ndarray  # internally, stored as an (N, 5) array
    _lut_func: LutCallable | None  # overrides if provided

    def __init__(
        self,
        stops: np.ndarray | Iterable[tuple[float, Color]] | None = None,
        *,
        lut_func: LutCallable | None = None,
        interpolation: Interpolation | bool = "linear",
    ) -> None:
        self._interpolation = _norm_interp(interpolation)
        self._lut_func: LutCallable | None = None
        if lut_func is not None:
            self._lut_func = lut_func
            if stops is not None:  # pragma: no cover
                warnings.warn(
                    "lut_func argument overrides stops argument. Don't pass both.",
                    stacklevel=2,
                )

            stops = np.linspace(0, 1, 256)
            colors = self._call_lut_func(stops)
            stop_colors = np.concatenate([stops[:, None], colors], axis=1)
            self._stops = stop_colors
        else:
            if stops is None:  # pragma: no cover
                raise ValueError("Must pass either stops or callable")

            # the internal representation is an (N, 5) array
            # the first column is the stop position, the next 4 are the RGBA values
            if isinstance(stops, np.ndarray):
                if len(stops.shape) != 2 or stops.shape[1] != 5:
                    raise ValueError("Expected (N, 5) array")  # pragma: no cover
                self._stops = stops
            else:
                self._stops = np.array([(p, *tuple(c)) for p, c in stops])

    def _call_lut_func(self, X: np.ndarray) -> np.ndarray:
        if self._lut_func is None:
            raise ValueError("No lut_func provided")  # pragma: no cover
        colors = np.atleast_2d(np.clip(self._lut_func(X), 0, 1))
        if colors.shape[1] == 3:
            colors = np.concatenate([colors, np.ones((len(X), 1))], axis=1)
        elif colors.shape[1] != 4:
            raise ValueError("lut_func must return RGB or RGBA values")
        return cast("np.ndarray", colors)

    @classmethod
    def parse(cls, colors: ColorStopsLike) -> ColorStops:
        """Parse any colorstops-like object into a ColorStops object.

        This is the more flexible constructor.
        see `_parse_colorstops` docstring for details.

        Parameters
        ----------
        colors : str | Iterable[Any]
            Colors and (optional) stop positions.

        Returns
        -------
        ColorStops
            A sequence of color stops.
        """
        return _parse_colorstops(colors, cls=cls)

    @classmethod
    def _from_uniform_stops(
        cls, stops: Sequence[tuple[float, Sequence[float]]]
    ) -> ColorStops:
        """Create a ColorStops object from a sequence of uniform stops.

        Faster constructor for a list of [(position, (r, g, b, a?)), ...] tuples.
        This performs no color checking, clipping, or normalization.
        """
        ary = np.asarray([(x, *rest) for x, rest in stops])
        if ary.shape[1] == 4:
            ary = np.concatenate([ary, np.ones((len(ary), 1))], axis=1)
        return cls(ary)

    @classmethod
    def _from_colorarray_like(cls, colors: ArrayLike) -> ColorStops:
        """Create a ColorStops object from a sequence of colors.

        Faster constructor for a list of [(r, g, b, a?), ...] colors
        This performs no color checking, clipping, or normalization.
        """
        ary = np.asarray(colors)
        if np.issubdtype(ary.dtype, np.integer):
            ary = ary / 255
        if ary.shape[1] == 3:
            ary = np.concatenate([ary, np.ones((len(ary), 1))], axis=1)
        stops = np.linspace(0, 1, len(ary))
        return cls(np.concatenate([stops[:, None], ary], axis=1))

    @property
    def stops(self) -> tuple[float, ...]:
        """Return tuple of color stop positions."""
        return tuple(self._stops[:, 0])

    @property
    def colors(self) -> tuple[Color, ...]:
        """Return all colors as Color objects."""
        return tuple(Color(c) for c in self.color_array)

    @property
    def color_array(self) -> np.ndarray:
        """Return an (N, 4) array of RGBA values."""
        return self._stops[:, 1:]

    def __len__(self) -> int:
        return len(self._stops)

    @overload
    def __getitem__(self, key: int) -> ColorStop: ...

    @overload
    def __getitem__(self, key: slice) -> ColorStops: ...

    @overload
    def __getitem__(self, key: tuple) -> np.ndarray: ...

    def __getitem__(
        self, key: int | slice | tuple
    ) -> ColorStop | ColorStops | np.ndarray:
        """Get an item or slice of the color stops.

        If key is an integer, return a single `ColorStop` tuple.
        If key is a slice, return a new `ColorStops` object.
        If key is a tuple, return a numpy array (standard numpy indexing).
        """
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(key, slice):
            return ColorStops(self._stops[key])
        if isinstance(key, tuple):
            return np.asarray(self)[key]  # type: ignore
        pos, *rgba = self._stops[key]
        return ColorStop(pos, Color(rgba))

    def __reversed__(self) -> Iterator[ColorStop]:
        # this for the reversed() builtin ... when iterating single
        # ColorStops.  But see the reversed() method below for when
        # you want to create a new ColorStops object that is "permantently"
        # reversed.
        for pos, *rgba in self._stops[::-1]:
            # reverse the colors, but not the positions
            yield ColorStop(1 - pos, Color(rgba))

    def __array__(self, dtype: npt.DTypeLike = None) -> np.ndarray:
        """Return (N, 5) array, N rows of (position, r, g, b, a)."""
        return self._stops if dtype is None else self._stops.astype(dtype)

    def __repr__(self) -> str:
        """Return a string representation of the ColorStops."""
        if self._lut_func is not None:
            f = self._lut_func
            rev = ""
            if self._is_reversed_lut_func(f):
                f = f.args[0]
                rev = " <reversed>"
            name = f"{f.__module__}{f.__qualname__}"
            return f"ColorStops(lut_func={name!r}{rev})"
        m = ",\n  ".join(repr((pos, Color(rgba))) for pos, *rgba in self._stops)
        return f"ColorStops(\n  {m}\n)"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, ColorStops):
            try:
                __o = ColorStops.parse(__o)  # type: ignore
            except Exception:
                return NotImplemented
        return np.allclose(self._stops, __o._stops)

    def to_lut(self, N: int = 256, gamma: float = 1.0) -> np.ndarray:
        """Create (N, 4) LUT of RGBA values from 0-1, interpolated between color stops.

        Parameters
        ----------
        N : int
            Number of colors to return.
        gamma : float
            Gamma correction to apply to the colors.
        """
        if self._interpolation == "nearest":
            return self.color_array

        if self._lut_func is not None:
            return self._call_lut_func(np.linspace(0, 1, N) ** gamma)

        # the 50 is a magic number... we're just saying "if a lot of colors are being
        # requested, and that number is one more than the number of stops, then just
        # return color_array without interpolation.  This is a bit of a hack, but it
        # avoids some edge cases of rounding errors.  Could be done better.
        if 50 < len(self._stops) == N + 1:
            # no interpolation needed
            return self.color_array
        return _interpolate_stops(N, self._stops, gamma)

    def to_css(
        self,
        max_stops: int | None = None,
        angle: int = 90,
        radial: bool = False,
        as_hex: bool = False,
    ) -> str:
        """Return a CSS representation of the color stops.

        Parameters
        ----------
        max_stops : int, optional
            May be used to limit the number of color stops in the css.
        angle : int, optional
            Angle of the gradient in degrees. by default 90. (ignored for radial)
        radial : bool, optional
            If `True`, return a radial gradient, by default False.
        as_hex : bool, optional
            If `True`, return colors as hex strings, by default use `rgba()` strings.
        """
        if max_stops and len(self._stops) > max_stops:
            stops = tuple(np.linspace(0, 1, max_stops))
            colors = tuple(Color(c) for c in self.to_lut(max_stops))
        else:
            stops, colors = self.stops, self.colors
        if not colors:
            return ""
        out = f"background: {colors[0].hex if as_hex else colors[0].rgba_string};\n"
        type_ = "radial" if radial else "linear"
        if self._interpolation == "nearest":
            # if we're using nearest interpolation, for css we can create double stops
            # with two colors to get the same effect.
            # https://blog.prototypr.io/css-only-multi-color-backgrounds-4d96a5569a20

            # FIXME: this actually just ignores stop info... but we should be able
            # to make non-interpolated css that isn't just evenly spaced.
            # I think we have the same problem with the real colormaps too though.
            # (mpl ListedColormap assumes even spacing too though, so this is unlikely
            # to be a problem in practice)
            midpoints = np.linspace(0, 1, len(colors) + 1)[1:-1]
            _midstops = []
            for m, (c1, c2) in zip(midpoints, zip(colors[:-1], colors[1:])):
                s1 = f"{c1.hex if as_hex else c1.rgba_string} {m*100:g}%"
                s2 = f"{c2.hex if as_hex else c2.rgba_string} {m*100:g}%"
                _midstops.extend([s1, s2])
            _stops = ", ".join(_midstops)
        else:
            _stops = ", ".join(
                [
                    f"{c.hex if as_hex else c.rgba_string} {s*100:g}%"
                    for c, s in zip(colors, stops)
                ]
            )
        angle_ = "" if radial else f"{angle}deg, "
        out += f"background: {type_}-gradient({angle_}{_stops});\n"
        return out

    # Helper ensuring picklability of the reversed cmap.
    @staticmethod
    def _reverser(func: LutCallable, x: NDArray) -> NDArray:
        return func(1 - x)

    def _is_reversed_lut_func(self, f: Callable) -> TypeGuard[partial]:
        return isinstance(f, partial) and f.func is self._reverser

    def reversed(self) -> ColorStops:
        """Return a new ColorStops object with reversed colors."""
        if (lut_func := self._lut_func) is not None:
            # check if we're already a reversed lut_func
            if self._is_reversed_lut_func(lut_func):
                # and "unpartialize" it if so
                return type(self)(lut_func=lut_func.args[0])
            else:
                # partial to maintain picklability
                rev_lutfunc = partial(self._reverser, lut_func)
            return type(self)(lut_func=rev_lutfunc)
        # invert the positions in the stops
        rev_stops = self._stops[::-1]
        rev_stops[:, 0] = 1 - rev_stops[:, 0]
        return type(self)(rev_stops)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from pydantic_core import core_schema

        schema = handler(Any)
        ser = core_schema.plain_serializer_function_ser_schema(
            lambda x: [(p, list(c)) for p, c in x]
        )
        return core_schema.no_info_after_validator_function(
            cls.parse, schema, serialization=ser
        )

    @classmethod
    def __get_validators__(cls) -> Iterator[Callable]:
        yield cls.parse  # pydantic validator

    def _json_encode(self) -> list:
        return cast(list, self._stops.tolist())


def _fill_stops(
    stops: Iterable[float | None],
    fill_mode: Literal["neighboring", "fractional"] = "neighboring",
) -> list[float]:
    """Fill in missing stop positions.

    Replace None values in the list of stop positions with values spaced evenly
    between the nearest non-`None` values.

    Parameters
    ----------
    stops : list[float | None]
        List of stop positions.
    fill_mode : {'neighboring', 'fractional'}, optional
        How to fill in missing stop positions.  If 'neighboring' (the default),
        missing positions will be evenly distributed between the closest specified
        neighboring positions.  If 'fractional', missing stop positions will be
        replaced with `index / (len(colors)-1)`.  For example:

        >>> s = ColorStops.parse(['r', 'y', (0.8,'g'), 'b'])
        >>> s.stops
        # 'y' is halfway between 'r' and 'g'
        (0.0, 0.4, 0.8, 1.0)
        >>> s = ColorStops.parse(['r', 'y', (0.8,'g'), 'b'], fill_mode='fractional')
        >>> s.stops
        # 'y' is 1/3 of the way between 0 and 1
        (0.0, 0.3333333333333333, 0.8, 1.0)

    Examples
    --------
    >>> fill_stops([0.0, None, 0.5, None, 1.0])
    [0.0, 0.25, 0.5, 0.75, 1.0]
    >>> fill_stops([None, None, None])
    [0.0, 0.5, 1.0]
    >>> fill_stops([None, None, 0.8, None, 1.0])
    [0.0, 0.4, 0.8, 0.9, 1.0]
    """
    if fill_mode not in {"neighboring", "fractional"}:
        raise ValueError(  # pragma: no cover
            f"fill_mode must be 'neighboring' or 'fractional', not {fill_mode!r}"
        )

    _stops = list(stops)
    if not _stops:
        return []  # pragma: no cover

    if fill_mode == "fractional":
        N = len(_stops) - 1
        return [i / N if s is None else s for i, s in enumerate(_stops)]

    # make edges 0-1 unless they are explicitly set
    if _stops[0] is None:
        _stops[0] = 0.0
    if _stops[-1] is None:
        _stops[-1] = 1.0

    out: list[float] = []
    last_val: tuple[int, float] = (0, 0.0)
    in_gap = False  # marks whether we are in a series of Nones
    for idx, stop in enumerate(_stops):
        if stop is not None:
            if in_gap:
                # if we are at the first value after a series of Nones, then
                # fill in the Nones with values spaced evenly between the
                # previous value and the current value.
                _idx, _stop = last_val
                filler = np.linspace(_stop, stop, idx - _idx + 1)
                out.extend(filler[1:])
                in_gap = False
            else:
                # otherwise, just append the current value
                out.append(stop)
            last_val = (idx, stop)
        else:
            in_gap = True
    return out


def _interpolate_stops(N: int, data: ArrayLike, gamma: float = 1.0) -> np.ndarray:
    """Intperpolate (R, C) array of values to an (N, C-1) LUT array.

    The input array must have at least 2 columns, where the first column is a
    monotonically increasing list of positions from 0 to 1, and the remaining columns
    are vector values to interpolate between (such as r, g, b, a values). For example:

        [[0.0, 0.0, 0.0, 0.0, 0.0],  # transparent black
         [0.5, 1.0, 0.0, 0.0, 1.0],  # opaque red
         [1.0, 1.0, 1.0, 1.0, 1.0]]  # opaque white

    (Note, this function does not assume 5 columns, and will work with any
    number of columns greater than 1.)

    The output array will have N rows, and C-1 columns (i.e. the first column will
    no longer represent positions, and each row will be an interpolated value of the
    remaining columns of the input array). For a color LUT, each row represents
    the color at an evenly spaced position along the color gradient, from 0 to 1.

    This array can be used to create a color map, or to apply a color gradient to data
    that has been normalized to the range 0-1. (e.g. lut.take(data * (N-1), axis=0))

    Parameters
    ----------
    N : int
        Number of interpolated values to generate in the output LUT.
    data : ArrayLike
        Array of (position, r, g, b, a) values.
    gamma : float, optional
        Gamma correction to apply to the output LUT, by default 1.0

    Returns
    -------
    lut : np.ndarray
        (N, 4) LUT of RGBA values, interpolated between color stops.
    """
    adata = np.atleast_2d(np.array(data))
    if adata.shape[1] < 2:  # pragma: no cover
        raise ValueError("data must have at least 2 columns")

    # make sure the first and last stops are at 0 and 1 ...
    # adding additional control points that copy the first/last color if needed
    if adata[0, 0] != 0.0:
        adata = np.vstack([[0.0, *adata[0, 1:]], adata])
    if adata[-1, 0] != 1.0:
        adata = np.vstack([adata, [1.0, *adata[-1, 1:]]])

    x = adata[:, 0]
    rgba = adata[:, 1:]

    # This is also validated in the ColorMap constructor...
    # so we can skip it here unless this becomes a public function
    # if (np.diff(x) < 0).any():  # pragma: no cover
    #     raise ValueError("Color stops must be in ascending position order")

    # begin generation of lookup table
    if N == 1:
        # convention: use the y = f(x=1) value for a 1-element lookup table
        lut = rgba[-1]
    else:
        # sourcery skip: extract-method
        # scale stop positions to the number of elements (-1) in the LUT
        x = x * (N - 1)
        # create evenly spaced LUT indices with gamma correction
        xind = np.linspace(0, 1, N) ** gamma
        # scale to the number of elements (-1) in the LUT, and exclude exterior values
        xind = ((N - 1) * xind)[1:-1]
        # Find the indices in the scaled positions array `x` that each element in
        # `xind` would need to be inserted before to maintain order.
        ind = np.searchsorted(x, xind)
        # calculate the fractional distance between the two values in `x` that
        # each element in `xind` is between. (this is the position at which we need
        # to sample between the neighboring color stops)
        frac_dist = (xind - x[ind - 1]) / (x[ind] - x[ind - 1])
        # calculate the color at each position in `xind` by linearly interpolating
        # the value at `frac_dist` between the neighboring color stops
        start = rgba[ind - 1]
        length = rgba[ind] - start
        interpolated_points = frac_dist[:, np.newaxis] * length + start
        # concatenate the first and last color stops with the interpolated values
        lut = np.concatenate([[rgba[0]], interpolated_points, [rgba[-1]]])

    # ensure that the lut is confined to values between 0 and 1 by clipping it
    return np.clip(lut, 0.0, 1.0)  # type: ignore


def _map_rgb(mappers: Iterable[LutCallable], ary: NDArray) -> NDArray:
    """Combine multiple LutCallables into single rgb array."""
    return np.stack([_g(np.asarray(ary)) for _g in mappers], axis=-1)


def _mpl_segmentdata_to_stops(
    data: MPLSegmentData, precision: int = 16, N: int = 256, gamma: float = 1.0
) -> list[ColorStopLike] | LutCallable:
    """Convert a matplotlib colormap segmentdata dict to a list of stops.

    Parameters
    ----------
    data : dict
        A matplotlib colormap segmentdata dict, with keys 'red', 'green', 'blue' and
        values that are either a sequence of (X, Y0, Y1) tuples, or a callable
        function that takes an array of indices and returns an array of values.
    precision : int, optional
        The number of decimal places to round the output values to, by default 16
    N : int, optional
        The number of values to generate for the output stops (only used if any value
        in the data dict is a callable), by default 256
    gamma : float, optional
        The gamma correction to apply to the output stops, by default 1.0 (only used
        if any value in the data dict is a callable)

    Returns
    -------
    stops : list[tuple[float, RGBTuple]]
        A list of (position, [r, g, b]) tuples.
    """
    if all(callable(v) for v in data.values()):
        funcs = (data["red"], data["green"], data["blue"])
        if "alpha" in data:
            return partial(_map_rgb, (*funcs, data["alpha"]))
        return partial(_map_rgb, funcs)
    if any(callable(v) for v in data.values()):
        raise ValueError(
            "All values in segmentdata dict must be either callable or a sequence"
        )
    keys = ("red", "green", "blue")
    rgb_stops = [[i[:2] for i in data[c]] for c in keys]  # type: ignore
    all_positions = np.array(sorted({i for n in rgb_stops for i, _ in n}))
    rgb = [np.interp(all_positions, *np.asarray(s).T) for s in rgb_stops]
    if "alpha" in data:
        _a = [i[:2] for i in cast("Sequence", data["alpha"])]
        alpha = np.interp(all_positions, *np.asarray(_a).T)
    else:
        alpha = np.ones_like(all_positions)

    rgba = np.stack([*rgb, alpha], axis=1)
    return [(a, tuple(b)) for a, b in zip(all_positions, rgba.tolist())]


def _make_identifier(name: str) -> str:
    """Return a valid Python identifier from a string."""
    out = "".join(c for c in name if c.isalnum() or c in ("_", "-", " ", ":"))
    return out.lower().replace(" ", "_").replace("-", "_").replace(":", "_")


def _is_mpl_segmentdata(obj: Any) -> TypeGuard[MPLSegmentData]:
    """Return True if obj is a matplotlib segmentdata dict."""
    return isinstance(obj, dict) and all(k in obj for k in ("red", "green", "blue"))


def _parse_colorstops(
    val: ColorStopsLike,
    cls: type[ColorStops] = ColorStops,
) -> ColorStops:
    """Parse `colors` into a sequence of color stops.

    Each item in `colors` can be a color, or a 2-tuple of (position, color), where
    position (the "stop" along a color gradient) is a float between 0 and 1.  Where
    not provided, color positions will be evenly distributed between neighboring
    specified positions (if `fill_mode` is 'neighboring') or will be replaced with
    `index / (len(colors)-1)` (if `fill_mode` is 'fractional').

    Colors can be expressed as anything that can be converted to a Color, including
    a string, or 3/4-sequence of RGB(A) values.

    Parameters
    ----------
    val : str | Iterable[Any]
        Colors and (optional) stop positions.
    cls : type, optional
        The class to instantiate, by default ColorStops

    Returns
    -------
    ColorStops
        A sequence of color stops.
    """
    if callable(val):
        return cls(lut_func=val)

    if isinstance(val, str):
        rev = val.endswith("_r")
        data = Colormap.catalog()[val[:-2] if rev else val]
        stops = _parse_colorstops(data.data, cls=cls)
        stops._interpolation = _norm_interp(data.interpolation)
        return stops.reversed() if rev else stops

    if isinstance(val, cls):
        return val

    _clr_seq: Sequence[ColorLike | ColorStopLike]
    if _is_mpl_segmentdata(val):
        _mpl_stops = _mpl_segmentdata_to_stops(val)
        if callable(_mpl_stops):
            return cls(lut_func=_mpl_stops)
        _clr_seq = _mpl_stops
    elif isinstance(val, dict):
        if not all(isinstance(x, Number) for x in val):
            raise ValueError(
                "If colors is a dict, it must be a mapping from position to color, "
                "or a matplotlib-style segmentdata dict (with 'red', 'green', and "
                "'blue' keys)."
            )
        val = cast("dict[float, ColorLike]", val)
        _clr_seq = [(x, val[x]) for x in sorted(val)]
    else:  # all other iterables
        _clr_seq = list(val)

    if len(_clr_seq) == 1:
        _clr_seq = [None, _clr_seq[0]]

    _positions: list[float | None] = []
    _colors: list[Color] = []
    for item in _clr_seq:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            # a 2-tuple cannot be a valid color, so it must be a stop
            _position, item = cast("tuple[float, ColorLike]", item)
        elif (isinstance(item, (tuple, list)) and len(item) == 5) or (
            isinstance(item, np.ndarray) and item.shape == (5,)
        ):
            # 5-element vector must be (position, r, g, b, a)
            _position, *item = cast("Sequence[float]", item)
        else:
            _position = None
        _positions.append(_position)
        _colors.append(Color(item))  # type: ignore  # this will raise if invalid

    if (np.diff([x for x in _positions if x is not None]) < 0).any():
        raise ValueError("Color stops must be in ascending position order")

    _stops = _fill_stops(_positions, "neighboring")  # TODO: expose fill_mode?
    return cls(zip(_stops, _colors))
