from typing import Any

import numpy as np
import pytest

from cmap._color import RGBA, RGBA8, Color, parse_int

try:
    import colour

    colourRed = colour.Color("red")
except ImportError:
    colourRed = "red"

try:
    import pydantic_extra_types.color

    pydanticRed = pydantic_extra_types.color.Color("red")
except ImportError:
    try:
        import pydantic.color

        pydanticRed = pydantic.color.Color("red")
    except ImportError:
        pydanticRed = "red"


@pytest.mark.parametrize(
    "color, expected",
    [
        ("royalblue", (65, 105, 225)),
        (Color("royalblue"), (65, 105, 225)),
        ("Royal Blue", (65, 105, 225)),
        ((65, 105, 225), (65, 105, 225)),
        ([65, 105, 225], (65, 105, 225)),
        (np.array([65, 105, 225]), (65, 105, 225)),
        (RGBA8(65, 105, 225), (65, 105, 225)),
        ("rgb(65, 105, 225)", (65, 105, 225)),
        ("rgb(65 105 225)", (65, 105, 225)),
        ("rgb(65,105,225)", (65, 105, 225)),
        ((65 / 255, 105 / 255, 225 / 255), (65, 105, 225)),
        ("#4169E1", (65, 105, 225)),
        ("#ABC", (170, 187, 204)),
        (0x4169E1, (65, 105, 225)),
        ("0x4169E133", (65, 105, 225, 0.2)),
        ("rgb(2, 3, 4)", (2, 3, 4)),
        ("rgb(100%, 0%, 0%)", (255, 0, 0)),
        ("rgb(100%,none, 0%)", (255, 0, 0)),
        ("rgba(2, 3, 4, 0.5)", (2, 3, 4, 0.5)),
        ("rgba(2,3,4,50%)", (2, 3, 4, 0.5)),
        ("rgb(-2, 3, 4)", (0, 3, 4)),
        ("rgb(100, 200, 300)", (100, 200, 255)),
        ("rgb(20, 10, 0, -10)", (20, 10, 0, 0)),
        ("rgb(100%, 200%, 300%)", (255, 255, 255)),
        ("rgb(100%, 200%, 300%)", (255, 255, 255)),
        ("rgb(128 none none / none)", (128, 0, 0, 0)),
        ("hsl(120, 100%, 50%)", (0, 255, 0)),
        ("hsla(120, 100%, 50%, 0.25)", (0, 255, 0, 0.25)),
        ("hsla(120, 100%, 50% / none)", (0, 255, 0, 0)),
        (RGBA(0, 1, 0, 0), (0, 255, 0, 0)),
        (RGBA8(0, 255, 0, 1), (0, 255, 0, 1)),
        (None, (0, 0, 0, 0)),
    ],
)
def test_rgb_parse(color: str, expected: tuple) -> None:
    assert RGBA8.parse(color)[: len(expected)] == expected
    assert RGBA.parse(color).to_8bit()[: len(expected)] == expected


REDS = (
    "red",
    "r",
    "#F00",
    "#FF0000",
    "#FF0000FF",
    "rgb(255, 0, 0)",
    "rgba(255, 0, 0)",
    "rgba(255, 0, 0, 1)",
    "hsl(0, 100%, 50%)",
    "hsla(0, 100%, 50%)",
    "hsla(0, 100%, 50%, 1)",
    Color("r"),
    (255, 0, 0),
    (1.0, 0.0, 0.0),
    [1.0, 0.0, 0.0],
    np.array([1.0, 0.0, 0.0]),
    np.array([255, 0, 0]),
    0xFF0000,
    16711680,
)


@pytest.mark.parametrize("arg", REDS, ids=str)
def test_red_args(arg: Any) -> None:
    assert Color(arg) is Color("red")


def test_int_ambiguity() -> None:
    assert Color((1.0, 0, 0)) is Color("red")
    assert Color((1, 0, 0)) is not Color("red")
    # the floating np.ndarray is always interpreted as 0-1
    assert Color(np.array([0, 128, 255, 0.5])) is not Color([0, 128, 255, 0.5])


def test_color_errors() -> None:
    with pytest.raises(ValueError, match="Invalid color string"):
        Color("rgb(100%, 200%, 300%, 400%, 500%)")
    with pytest.raises(ValueError, match="Invalid color string"):
        Color("seven")
    with pytest.raises(TypeError, match="Cannot convert typ"):
        Color(1.2)  # type: ignore
    with pytest.raises(AttributeError, match="Color is immutable"):
        Color("red")._rgba = (0, 1, 2, 3)  # type: ignore


def test_rgb_conversions() -> None:
    # this test is very sensitive to rounding errors
    rgba = RGBA8(59, 84, 226, 0.6)
    assert rgba == rgba.to_float().to_8bit()
    assert rgba == rgba.to_hsl().to_rgba().to_8bit()
    assert rgba == rgba.to_hsv().to_rgba().to_8bit()
    assert int(rgba.to_hsl().in_degrees()[0]) == 231
    assert rgba.to_hex() == rgba.to_float().to_hex() == "#3B54E299"
    assert str(rgba) == str(rgba.to_float()) == "#3B54E299"


def test_color_conversions() -> None:
    color = Color("red")
    np.testing.assert_array_equal(np.asarray(color), (1, 0, 0, 1))
    assert color.hsl == (0, 1, 0.5, 1)
    assert color.hsv == (0, 1, 1, 1)
    assert color.alpha == 1
    assert color.hex == "#FF0000"
    assert color.rgba == (1, 0, 0, 1)
    assert color.rgba8 == (255, 0, 0, 1)
    assert color.rgba_string == "rgb(255, 0, 0)"
    assert Color((1.0, 1.0, 1.0, 0.5)).rgba_string == "rgba(255, 255, 255, 0.5)"
    assert color == "#FF0000FF"
    assert color == "#FF0000"
    assert color == Color("r")
    assert color != 1
    assert color != {"1234"}
    assert str(color) == "red"
    assert repr(Color((0.1, 0.2, -0.1))) == "Color((0.1, 0.2, 0.0))"


def test_copy() -> None:
    """test various copy and serdes operations"""
    import pickle
    from copy import copy, deepcopy
    from weakref import ref

    color = Color("red")
    assert copy(color) is color
    assert deepcopy(color) is color
    assert pickle.loads(pickle.dumps(color)) is color  # noqa: S301
    assert ref(color)() is color


def test_to_array_in_list() -> None:
    """Test that colors in a list get converted when using asarray"""
    ary = np.asarray([Color("r"), Color("g"), Color("b")])
    assert ary.shape == (3, 4)
    assert np.array_equal(ary, np.array([[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1]]))

    # seemingly unrelated, but __getitem__ is apparently necessary for the above,
    # but not actually called... so we test it here
    assert Color("r")[0] == 1


def test_hashable():
    assert hash(Color("red")) == hash(Color("red"))
    assert hash(Color("red")) != hash(Color("blue"))


def test_parse_int():
    # Test parsing a 24-bit integer value
    assert parse_int(0xFF00FF, "rgb") == RGBA(1.0, 0.0, 1.0, 1.0)

    # Test parsing a 32-bit integer value with alpha
    assert parse_int(0x00FF00FF, "rgba") == RGBA(0.0, 1.0, 0.0, 1.0)

    # Test parsing a 16-bit integer value with custom format
    assert parse_int(0x0FF, "bgr", bits_per_component=4) == RGBA(1.0, 1.0, 0.0, 1.0)

    expect = RGBA8(123, 255, 0)
    assert parse_int(0x7FE0, "rgb", bits_per_component=[5, 6, 5]).to_8bit() == expect

    # # Test parsing an invalid format
    with pytest.raises(ValueError):
        parse_int(0x7FE0, "rgbx")

    # Test parsing an invalid number of bits per component
    with pytest.raises(ValueError):
        parse_int(0x7FE0, "rgb", bits_per_component=[5, 5])


@pytest.mark.parametrize("input", [0xFF00FF, 0x00FF00FF, 0x0FF, 0x7FE0])
@pytest.mark.parametrize("fmt", ["rgb", "rgba", "bgr"])
def test_round_trip(input: int, fmt: str):
    assert Color.from_int(input, fmt).to_int(fmt) == input
