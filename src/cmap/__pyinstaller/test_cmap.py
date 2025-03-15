from PyInstaller.utils.conftest import *  # noqa
from typing import Any


def test_pyi_cmap_data(pyi_builder: Any) -> None:
    pyi_builder.test_source("""
    import cmap
    assert isisnstance(cmap.Colormap('viridis'), cmap.Colormap)
    assert isisnstance(cmap.Colormap('crameri:acton'), cmap.Colormap)
    """)
