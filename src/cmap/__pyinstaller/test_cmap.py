from PyInstaller.utils.conftest import pyi_builder, pyi_modgraph  # noqa
from typing import Any


def test_pyi_cmap_data(pyi_builder: Any) -> None:  # noqa: F811
    pyi_builder.test_source("""
    import cmap
    assert isinstance(cmap.Colormap('viridis'), cmap.Colormap)
    assert isinstance(cmap.Colormap('crameri:acton'), cmap.Colormap)
    """)
