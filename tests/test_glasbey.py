from __future__ import annotations

import sys
from contextlib import nullcontext
from typing import Literal

import pytest


@pytest.fixture(params=(False, True), ids=lambda x: "numba" if x else "no_numba")
def use_numba(request, monkeypatch) -> bool:
    sys.modules.pop("numba", None)
    sys.modules.pop("cmap.data.glasbey", None)
    sys.modules.pop("cmap.data.glasbey._internals", None)
    if not request.param:
        monkeypatch.setitem(sys.modules, "numba", None)
    else:
        pytest.importorskip("numba", reason="numba not installed")
    yield request.param


@pytest.mark.parametrize("grid_size", [36, (36, 36, 36)])
@pytest.mark.parametrize("grid_space", ["RGB", "JCh"])
@pytest.mark.parametrize("cvd_severity", [None, 0.5], ids=("no_cvd", "cvd"))
def test_glasbey_create_palette(
    use_numba: bool,
    grid_space: Literal["RGB", "JCh"],
    grid_size: int | tuple[int, int, int],
    cvd_severity: float | None,
) -> None:
    pytest.importorskip("colorspacious")
    with nullcontext() if use_numba else pytest.warns(UserWarning):
        from cmap.data.glasbey import create_palette

        create_palette(
            palette_size=256 if use_numba else 4,
            grid_space=grid_space,
            grid_size=grid_size,
            cvd_severity=cvd_severity,
        )
