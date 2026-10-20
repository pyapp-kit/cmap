import inspect
import pickle
import sys
from copy import copy, deepcopy
from functools import partial
from typing import Any

import numpy as np
import numpy.testing as npt
import pytest

from cmap import Color, Colormap
from cmap._colormap import ColorStop, ColorStops, _fill_stops
from cmap.data.matlab import prism

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
    for x, e in zip(cmap.color_stops.colors, "rmb", strict=False):
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


def test_colorstops_lut_func() -> None:
    def f(x: np.ndarray) -> np.ndarray:
        return np.stack([x, 2 * x, -x], axis=-1)

    cs = ColorStops(lut_func=f)
    assert cs.lut_func is f
    assert Colormap("prism").color_stops.lut_func is prism
    assert Colormap("viridis").color_stops.lut_func is None
    x = np.array([0.1234])
    reversed_func = cs.reversed().lut_func
    assert reversed_func is not None
    npt.assert_allclose(reversed_func(x), f(1 - x), rtol=0, atol=1e-12)
    with pytest.raises(AttributeError):
        cs.lut_func = f


def test_colorstops_reversed_does_not_mutate_source() -> None:
    stops = ColorStops.parse(["red", "green", "blue"])
    before = np.asarray(stops).copy()

    stops.reversed()

    npt.assert_array_equal(np.asarray(stops), before)


def test_r_suffix_is_kept_in_the_name() -> None:
    cm = Colormap("viridis_r")
    assert cm.name == "bids:viridis_r"
    assert cm.identifier == "bids_viridis_r"
    assert cm.identifier != Colormap("viridis").identifier
    assert cm.reversed().name == "bids:viridis"
    assert Colormap("viridis").reversed().name == cm.name
    assert Colormap("viridis_r", name="mine").name == "mine"


def test_construction_does_not_change_source_interpolation() -> None:
    stops = Colormap(["red", "blue"], interpolation="nearest").color_stops
    before = stops.to_lut(4).copy()

    Colormap(stops, interpolation="linear")

    npt.assert_array_equal(stops.to_lut(4), before)


def test_with_extremes_preserves_interpolation() -> None:
    cmap = Colormap(["red", "blue"], interpolation="nearest")

    new = cmap.with_extremes(bad="red")

    assert new.interpolation == "nearest"
    npt.assert_array_equal(new.lut(4), cmap.lut(4))


def test_colormap_copy() -> None:
    """Test Colormap copy."""
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
    new_order = ">" if sys.byteorder == "little" else "<"
    swapped = img.view(img.dtype.newbyteorder(new_order))
    assert cmap1(swapped).shape == (10, 10, 4)


def test_non_native_byte_order_maps_the_same_colors() -> None:
    cmap = Colormap(["red", "blue"], under="green", over="yellow", bad="black")
    native = np.array([-0.5, 0.0, 0.5, 1.0, 1.5, np.nan])
    non_native = native.astype(native.dtype.newbyteorder())

    npt.assert_array_equal(cmap(non_native), cmap(native))


def test_colormap_masked_array_with_unmasked_nan() -> None:
    cmap = Colormap("viridis", bad="red")
    mask = [True, False, False, False]
    data = np.ma.masked_array([0.0, 0.25, np.nan, 1.0], mask=mask)

    rgba = cmap(data)

    npt.assert_array_equal(rgba[0], Color("red").rgba)  # masked
    npt.assert_array_equal(rgba[2], Color("red").rgba)  # nan, not masked
    npt.assert_array_equal(rgba[[1, 3]], cmap(np.array([0.25, 1.0])))
    npt.assert_array_equal(data.mask, mask)

    # an all-false mask takes the same path as a plain array
    all_false = np.ma.masked_array([0.25, np.nan], mask=[False, False])
    npt.assert_array_equal(cmap(all_false), cmap(np.array([0.25, np.nan])))


def test_exceptional_colors() -> None:
    cmap = Colormap(
        ["red", "blue"],
        under="green",
        over="yellow",
        bad="black",
        neg_inf="cyan",
        pos_inf="magenta",
        nan="white",
    )
    mask = [False] * 6 + [True] * 3
    data = np.ma.masked_array(
        [-np.inf, -0.5, 0.5, 1.5, np.inf, np.nan, np.inf, np.nan, 0.25], mask=mask
    )
    expect = np.array(
        [
            Color("cyan").rgba,  # -inf
            Color("green").rgba,  # under range, finite
            Colormap(["red", "blue"])(0.5).rgba,  # in range
            Color("yellow").rgba,  # over range, finite
            Color("magenta").rgba,  # +inf
            Color("white").rgba,  # nan, not masked
            Color("black").rgba,  # masked +inf -> bad
            Color("black").rgba,  # masked nan -> bad
            Color("black").rgba,  # masked -> bad
        ]
    )

    npt.assert_array_equal(cmap(data), expect)
    npt.assert_array_equal(cmap(data, bytes=True), (expect * 255).astype(np.uint8))
    npt.assert_array_equal(data.mask, mask)


def test_exceptional_colors_fall_back_to_the_legacy_extremes() -> None:
    cmap = Colormap(["red", "blue"], under="green", over="yellow", bad="black")
    data = np.ma.masked_array(
        [-np.inf, np.inf, np.nan, 0.5], mask=[False, False, False, True]
    )
    legacy = [
        Color("green").rgba,  # -inf -> under
        Color("yellow").rgba,  # +inf -> over
        Color("black").rgba,  # nan -> bad
        Color("black").rgba,  # masked -> bad
    ]
    npt.assert_array_equal(cmap(data), legacy)

    # setting one leaves the other exceptional classes on their legacy destinations
    one = cmap.with_extremes(under="green", over="yellow", bad="black", nan="white")
    npt.assert_array_equal(one(data), [*legacy[:2], Color("white").rgba, legacy[3]])


def test_finite_values_that_overflow_when_scaled_are_not_infinite() -> None:
    # float16 65504 becomes inf once multiplied by N, but it is over-range, not infinite
    cmap = Colormap(
        ["red", "blue"], under="green", over="yellow", neg_inf="cyan", pos_inf="magenta"
    )
    data = np.array([65504, -65504, np.inf, -np.inf], dtype=np.float16)
    with np.errstate(over="ignore"):
        rgba = cmap(data)
    npt.assert_array_equal(
        rgba,
        [
            Color("yellow").rgba,
            Color("green").rgba,
            Color("magenta").rgba,
            Color("cyan").rgba,
        ],
    )


@pytest.mark.parametrize("exceptional", [False, True])
def test_masked_dtypes_keep_their_existing_behavior(exceptional: bool) -> None:
    extra = {"neg_inf": "cyan", "pos_inf": "magenta", "nan": "white"}
    cmap = Colormap(["red", "blue"], bad="black", **(extra if exceptional else {}))
    bad = Color("black").rgba

    npt.assert_array_equal(cmap(np.ma.masked_array([0, 1], mask=[True, False]))[0], bad)

    obj = np.ma.masked_array(np.array([0.25, 0.5], dtype=object), mask=[True, False])
    npt.assert_array_equal(cmap(obj)[0], bad)

    npt.assert_array_equal(cmap(np.ma.masked_array(0.5, mask=True)).rgba, bad)
    npt.assert_array_equal(cmap(np.ma.masked_array(np.inf, mask=True)).rgba, bad)
    npt.assert_array_equal(cmap(np.ma.masked_array([-np.inf], mask=[True])), [bad])


def test_exceptional_colors_scalar_input() -> None:
    cmap = Colormap(
        ["red", "blue"], neg_inf="cyan", pos_inf="magenta", nan="white", bad="black"
    )
    for value, name in [(-np.inf, "cyan"), (np.inf, "magenta"), (np.nan, "white")]:
        result = cmap(value)
        assert isinstance(result, Color)
        assert result == Color(name)


def test_exceptional_colors_do_not_affect_integer_input() -> None:
    plain = Colormap(["red", "blue"], under="green", over="yellow")
    cmap = Colormap(
        ["red", "blue"],
        under="green",
        over="yellow",
        neg_inf="cyan",
        pos_inf="magenta",
        nan="white",
    )
    data = np.array([-1, 0, 100, 255, 256, 1000])
    npt.assert_array_equal(cmap(data), plain(data))


@pytest.mark.parametrize("field", ["neg_inf", "pos_inf", "nan"])
def test_exceptional_colors_are_colormap_state(field: str) -> None:
    plain = Colormap(["red", "blue"])
    cmap = Colormap(["red", "blue"], **{field: "orange"})

    assert cmap != plain
    assert plain.with_extremes(**{field: "orange"}) == cmap
    assert cmap.shifted(1) == cmap
    assert field in cmap._repr_html_()


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


def test_interp_arg_passed_to_stops() -> None:
    cm = Colormap(["#364B9A", "#4A7BB7", "#6EA6CD", "#98CAE1"], interpolation=False)
    assert cm.color_stops._interpolation == "nearest"

    cm = Colormap(["#364B9A", "#4A7BB7", "#6EA6CD", "#98CAE1"])
    assert cm.color_stops._interpolation == "linear"


def test_with_extremes() -> None:
    cm = Colormap(["red", "blue"], under="green", over="yellow", bad="black")
    cm2 = Colormap(["red", "blue"]).with_extremes(
        under="green", over="yellow", bad="black"
    )
    assert cm == cm2

    assert cm2.under_color == cm.under_color == Color("green")
    assert "under" in cm2._repr_html_()


def _configured() -> Colormap:
    return Colormap(
        ["red", "blue"],
        name="foo",
        category="sequential",
        interpolation="nearest",
        under="green",
        over="yellow",
        bad="black",
        neg_inf="cyan",
        pos_inf="magenta",
        nan="white",
    )


def test_with_extremes_preserves_what_is_not_passed() -> None:
    cm = Colormap(["red", "blue"], identifier="my_id", under="green", nan="white")

    new = cm.with_extremes(over="yellow")

    assert new.under_color == Color("green")
    assert new.nan_color == Color("white")
    assert new.over_color == Color("yellow")
    assert new.identifier == "my_id"


def test_reversed_preserves_state_and_swaps_the_directional_colors() -> None:
    cm = _configured()
    # the comparisons with `cm` below only catch a dropped or unswapped field if
    # every field is non-default and the extreme colors are all distinct
    extremes = [cm.under_color, cm.over_color, cm.bad_color]
    extremes += [cm.neg_inf_color, cm.pos_inf_color, cm.nan_color]
    assert None not in extremes and len(set(extremes)) == len(extremes)
    assert cm.category is not None and cm.interpolation != "linear"

    rev = cm.reversed()

    assert rev.name == f"{cm.name}_r"
    assert rev.category == cm.category
    assert rev.interpolation == cm.interpolation
    # under/over and neg_inf/pos_inf name the ends they extend, so they follow them
    assert rev.under_color == cm.over_color
    assert rev.over_color == cm.under_color
    assert rev.neg_inf_color == cm.pos_inf_color
    assert rev.pos_inf_color == cm.neg_inf_color
    assert rev.bad_color == cm.bad_color
    assert rev.nan_color == cm.nan_color
    assert rev.reversed() == cm


# one catalog entry per kind of state that "_r" and reversed() could disagree on
@pytest.mark.parametrize(
    "name",
    [
        "napari:HiLo",  # under/over in the record, which must swap
        "tab10",  # nearest interpolation
        "napari:nan",  # bad in the record
    ],
)
def test_reversed_agrees_with_the_r_suffix(name: str) -> None:
    assert Colormap(name).reversed() == Colormap(f"{name}_r")


def test_r_suffix_keeps_explicit_directional_colors() -> None:
    # the record's colors swap; an explicit argument names the end it lands on
    assert Colormap("napari:HiLo_r", under="green").under_color == Color("green")


def test_pickle_preserves_constructor_state() -> None:
    cm = _configured()

    rt = pickle.loads(pickle.dumps(cm))  # noqa: S301

    assert rt == cm
    assert (rt.name, rt.identifier, rt.category, rt.interpolation) == (
        cm.name,
        cm.identifier,
        cm.category,
        cm.interpolation,
    )


@pytest.mark.parametrize("name", ["viridis", "viridis_r", "napari:HiLo_r"])
def test_copies_of_a_catalog_colormap_keep_its_info(name: str) -> None:
    cm = Colormap(name)

    for copied in (pickle.loads(pickle.dumps(cm)), copy(cm), deepcopy(cm)):  # noqa: S301
        assert copied == cm
        assert copied.name == cm.name
        assert copied.info is not None and copied.info == cm.info


# a sample for every constructor argument besides `value`.  A new argument fails the
# test below until it has a sample here, and that sample fails it until the argument
# is in the overrides that `Colormap.__init__` checks before recording a catalog name.
_ARGUMENT_SAMPLES: dict[str, Any] = {
    "name": "renamed",
    "identifier": "renamed",
    "category": "sequential",
    "interpolation": False,
    "under": "red",
    "over": "red",
    "bad": "red",
    "neg_inf": "red",
    "pos_inf": "red",
    "nan": "red",
    "cmap_kwargs": {"start": 1.0},
}


def test_any_constructor_argument_disables_the_catalog_name() -> None:
    params = set(inspect.signature(Colormap).parameters) - {"value"}
    assert params == set(_ARGUMENT_SAMPLES)

    assert Colormap("cubehelix")._catalog_name == "cubehelix:cubehelix"
    for arg, sample in _ARGUMENT_SAMPLES.items():
        cm = Colormap("cubehelix", **{arg: sample})
        assert cm._catalog_name is None, f"{arg}= is not treated as an override"


def test_copies_of_a_callable_colormap_stay_callable() -> None:
    # as_dict() samples the function into 256 stops; a copy must keep the function
    cm = Colormap("cubehelix", cmap_kwargs={"start": 1.0, "rotation": -1.0})

    for copied in (pickle.loads(pickle.dumps(cm)), copy(cm), deepcopy(cm)):  # noqa: S301
        npt.assert_array_equal(copied.lut(17, gamma=2), cm.lut(17, gamma=2))


def test_as_dict_round_trip() -> None:
    plain = Colormap(["red", "blue"])
    assert set(plain.as_dict()) == {"name", "identifier", "category", "value"}

    cm = _configured()
    d = cm.as_dict()

    assert d["interpolation"] == "nearest"
    assert d["nan"] == list(Color("white"))
    assert Colormap(**d) == cm


def test_shifted() -> None:
    cm = Colormap(["red", "blue", "yellow"])
    assert cm.shifted(1) == cm
    assert "shifted0.3" in cm.shifted(0.3).name
    # two shifts of 0.5 should give the original array
    assert cm.shifted().shifted() == cm

    wrapped = cm.shifted(0.2, mode="wrap")
    assert wrapped == Colormap([(0.2, "yellow"), (0.2, "red"), (0.7, "blue")])
    clipped = cm.shifted(0.5, mode="clip")
    assert clipped == Colormap([(0.5, "red"), (1, "blue")])

    cm = Colormap("viridis")
    # forward and backward shifts should cancel out
    assert cm.shifted(0.5).shifted(-0.5) == cm
    # two shifts of 0.5 should give the original array
    assert cm.shifted().shifted() == cm


def test_function_colormap_with_cmap_kwargs() -> None:
    # construct cubehelix with custom parameters
    ch = Colormap("cubehelix", cmap_kwargs={"start": 1.0, "rotation": -1.0})

    # values should be different from default cubehelix
    default_ch = Colormap("cubehelix")
    assert ch(0.5) != default_ch(0.5)


def test_invalid_function_colormap_with_cmap_kwargs() -> None:
    # providing cmap_kwargs to a non-callable colormap should raise TypeError
    with pytest.raises(TypeError, match=r"Cannot apply cmap_kwargs to colormap"):
        Colormap("viridis", cmap_kwargs={"param": 1.0})


def test_scalar_bytes() -> None:
    cm = Colormap("viridis")
    expect = cm(np.array([0.5]), bytes=True)[0]
    for x in (0.5, np.float64(0.5), np.array(0.5)):
        rgba = cm(x, bytes=True)
        assert isinstance(rgba, tuple)
        assert rgba == tuple(expect)
        assert all(isinstance(v, np.uint8) for v in rgba)
    assert isinstance(cm(0.5), Color)
