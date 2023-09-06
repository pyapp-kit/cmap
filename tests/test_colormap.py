import sys
from functools import partial
from typing import Any

import numpy as np
import numpy.testing as npt
import pytest

from cmap import Color, Colormap
from cmap._colormap import ColorStop, ColorStops, _fill_stops

DATA = [
    [0.0, 1.0, 0.0, 0.0, 1.0],
    [0.25, 0.0, 0.50196078, 1.0, 0.5],
    [0.5, 1.0, 0.0, 1.0, 1.0],
    [0.9, 0.0, 0.0, 1.0, 1.0],
]
EXPECT = ColorStops(np.array(DATA))
SEGDICT = {
    "red": [[x[0], x[1], x[1]] for x in DATA],
    "green": [[x[0], x[2], x[2]] for x in DATA],
    "blue": [[x[0], x[3], x[3]] for x in DATA],
    "alpha": [[x[0], x[4], x[4]] for x in DATA],
}


@pytest.mark.parametrize(
    "color_stops",
    [
        ["red", (0, 128, 255, 0.5), (0.5, "m"), (0.9, "blue")],
        EXPECT._stops.tolist(),
        EXPECT._stops,
        DATA,
        np.array(DATA),
        {k: v for k, *v in DATA},
        SEGDICT,
    ],
)
def test_parse_colorstops(color_stops: Any) -> None:
    assert ColorStops.parse(color_stops) == EXPECT
    assert Colormap(color_stops).color_stops == EXPECT


@pytest.mark.parametrize(
    "color_stops",
    ["red", "red_r", list("rgb"), ["r", (0, "#00f"), (0.5, "m"), (0.9, "b")]],
)
def test_misc_colormap_args(color_stops: Any) -> None:
    assert Colormap(color_stops)


def test_colormap() -> None:
    """Test Colormap."""
    cmap = Colormap(["red", "magenta", "blue"], name="mymap")
    assert cmap(0.0) == (1.0, 0, 0, 1.0)
    assert cmap(0.0) is Color("r")
    assert cmap(0.5, N=255) == (1.0, 0, 1.0, 1.0)
    assert cmap(0.5, N=255) is Color("m")
    assert cmap(1.0) == (0, 0, 1.0, 1.0)
    assert cmap(1.0) is Color("b")
    assert cmap(1.5) == (0, 0, 1.0, 1.0)
    assert repr(cmap) == "Colormap(name='mymap', <3 colors>)"

    # also test with a sequence
    npt.assert_array_equal(
        cmap([0, 0.5, 1.0], N=255), [(1, 0, 0, 1), (1, 0, 1, 1), (0, 0, 1, 1)]
    )


def test_colorstops() -> None:
    cmap = Colormap(["red", "magenta", "blue"])
    assert cmap.color_stops.stops == (0, 0.5, 1.0)
    assert cmap.color_stops != {"1234"}  # just check a random comparison
    for x, e in zip(cmap.color_stops.colors, "rmb"):
        assert isinstance(x, Color)
        assert x == e

    assert isinstance(cmap.color_stops[:], ColorStops)
    assert isinstance(cmap.color_stops[0], ColorStop)
    assert isinstance(cmap.color_stops[0, 1:], np.ndarray)

    assert repr(cmap.color_stops) == (
        "ColorStops(\n"
        "  (0.0, Color('red')),\n"
        "  (0.5, Color('magenta')),\n"
        "  (1.0, Color('blue'))\n"
        ")"
    )

    assert reversed(cmap.color_stops) == ColorStops.parse(["b", "m", "r"])


def test_colormap_copy() -> None:
    """Test Colormap copy."""
    import pickle
    from copy import copy, deepcopy

    cmap1 = Colormap(["red", "magenta", "blue"])
    cmap2 = Colormap(["r", (0.5, "magenta"), "b"])
    assert cmap1 == cmap2
    assert copy(cmap1) == cmap1
    assert deepcopy(cmap1) == cmap1
    assert cmap1 == ["r", "m", "b"]
    assert cmap1 == ["r", (0.5, "m"), "b"]
    assert cmap1 == pickle.loads(pickle.dumps(cmap1)) == cmap2  # noqa: S301
    assert cmap1 != {"1234"}


def test_colormap_errors() -> None:
    with pytest.raises(ValueError, match="Colormap 'bad_string' not found"):
        Colormap("bad_string")
    with pytest.raises(AttributeError, match="Colormap is immutable"):
        Colormap("red")._lut_cache = {}
    with pytest.raises(ValueError, match="If colors is a dict"):
        Colormap({"invalid": "dict"})
    with pytest.raises(ValueError, match="Color stops must be in ascending position"):
        Colormap([(0.8, "r"), (0.2, "b")])


def test_colormap_methods() -> None:
    cmap1 = Colormap(["red", "magenta", "blue"])
    assert cmap1 == [(0, "r"), (0.5, "m"), (1, "b")]
    assert list(cmap1.color_stops) == [(0, "r"), (0.5, "m"), (1, "b")]
    assert Colormap(reversed(cmap1.color_stops)) == Colormap(["b", "m", "r"])
    assert list(cmap1.iter_colors(3)) == [Color("r"), Color("m"), Color("b")]


def test_colormap_apply() -> None:
    cmap1 = Colormap(["red", "magenta", "blue"])
    img = np.zeros((10, 10))
    assert cmap1(img).shape == (10, 10, 4)
    # non-native byte order
    assert cmap1(img.byteswap().newbyteorder()).shape == (10, 10, 4)


def test_fill_stops() -> None:
    assert _fill_stops([None, None, None]) == [0, 0.5, 1.0]
    assert _fill_stops([None, 0.8, None]) == [0, 0.8, 1.0]
    assert _fill_stops([None, None, 0.8, None]) == [0, 0.4, 0.8, 1.0]
    assert _fill_stops([None, None, 0.8, None], "fractional") == [0, 1 / 3, 0.8, 1.0]
    assert _fill_stops([None, None, 0.8], "neighboring") == [0, 0.4, 0.8]
    assert _fill_stops([None, None, 0.8], "fractional") == [0, 0.5, 0.8]


def test_to_lut() -> None:
    # lut() does the interpolation
    cmap = Colormap(["red", "blue"])
    npt.assert_allclose(cmap.lut(1), [0, 0, 1, 1])  # single color
    npt.assert_allclose(cmap.lut(2), [(1, 0, 0, 1), (0, 0, 1, 1)])
    npt.assert_allclose(cmap.lut(3), [(1, 0, 0, 1), (0.5, 0, 0.5, 1), (0, 0, 1, 1)])
    npt.assert_allclose(
        cmap.lut(3, gamma=2), [(1, 0, 0, 1), (0.75, 0, 0.25, 1), (0, 0, 1, 1)]
    )

    # we pad the ends with 0-1 if not explicitly specified
    cmap = Colormap([(0.2, "r"), (0.8, "b")])
    npt.assert_allclose(cmap.lut(3), [(1, 0, 0, 1), (0.5, 0, 0.5, 1), (0, 0, 1, 1)])


def test_mpl_segment_conversion() -> None:
    # just here to fill out coverage
    _cm = pytest.importorskip("matplotlib._cm")
    from cmap._colormap import _mpl_segmentdata_to_stops

    for val in vars(_cm).values():
        if isinstance(val, dict) and "red" in val:
            assert isinstance(_mpl_segmentdata_to_stops(val), (list, partial))


@pytest.fixture(params=(True, False))
def with_or_without_PIL(request, monkeypatch):
    if not request.param:
        monkeypatch.setitem(sys.modules, "PIL", None)
    return request.param


def test_cmap_info() -> None:
    cm = Colormap("viridis")
    assert cm.info
    assert cm.interpolation == "linear"
    assert cm.info.qualified_name == "bids:viridis"
    assert "matplotlib:viridis" in cm.info.aliases
    assert "viridis" in cm.info.aliases

    assert Colormap("accent").interpolation == "nearest"


@pytest.mark.usefixtures("with_or_without_PIL")
def test_repr_notebook() -> None:
    cm = Colormap("viridis")
    assert "viridis" in cm._repr_html_()
    assert isinstance(cm._repr_png_(), bytes)


def test_cmap_from_cmap() -> None:
    cm = Colormap(("red", "blue"), name="mymap")
    cm2 = Colormap(cm)
    assert cm2.name == "mymap"
