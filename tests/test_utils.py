import numpy as np
import pytest

try:
    from matplotlib.figure import Figure as MplFigure
except ImportError:
    MplFigure = None

from cmap import Colormap, _util

CMAP_NAME = "viridis"
CMAP_INSTANCE = Colormap(CMAP_NAME)


def test_ensure_cmap() -> None:
    cm = _util._ensure_cmap(CMAP_NAME)
    assert isinstance(cm, Colormap)
    cm2 = _util._ensure_cmap(cm)
    assert cm is cm2

@pytest.mark.skipif(MplFigure is None, reason="matplotlib not installed")
def test_plot() -> None:
    fig = _util.plot_color_gradients([CMAP_NAME], compare=True)
    assert isinstance(fig, MplFigure)


@pytest.mark.skipif(MplFigure is None, reason="matplotlib not installed")
def test_plot_rgb() -> None:
    fig = _util.plot_rgb(CMAP_NAME)
    assert isinstance(fig, MplFigure)


def test_calc_lightness() -> None:
    pytest.importorskip("colorspacious")
    lightness = _util.calc_lightness(CMAP_NAME)
    assert isinstance(lightness, np.ndarray)


@pytest.mark.skipif(MplFigure is None, reason="matplotlib not installed")
def test_plot_lightness() -> None:
    pytest.importorskip("colorspacious")
    fig = _util.plot_lightness(CMAP_NAME)
    assert isinstance(fig, MplFigure)


def test_hsv_to_rgb() -> None:
    rgb = _util.hsv_to_rgb([0.5, 0.5, 0.5])
    assert isinstance(rgb, np.ndarray)

    rgb = _util.hsv_to_rgb([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]])
    assert isinstance(rgb, np.ndarray)

    with pytest.raises(ValueError):
        _util.hsv_to_rgb([0.5, 0.5, 0.5, 0.6])


def test_sineramp() -> None:
    ramp = _util.sineramp()
    assert isinstance(ramp, np.ndarray)

    ramp = _util.sineramp(128)
    assert isinstance(ramp, np.ndarray)


def test_circlesineramp() -> None:
    ramp = _util.circlesineramp()
    assert isinstance(ramp, np.ndarray)

    ramp = _util.circlesineramp(128)
    assert isinstance(ramp, np.ndarray)


def test_report() -> None:
    pytest.importorskip("colorspacious")
    report = _util.report(CMAP_INSTANCE)
    assert isinstance(report, dict)

    report2 = _util.report(Colormap("red"))
    assert isinstance(report2, dict)
