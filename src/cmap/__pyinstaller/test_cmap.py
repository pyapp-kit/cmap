from typing import Any


def test_pyi_cmap_data(pyi_builder: Any) -> None:
    pyi_builder.test_source("""
    import cmap
    assert isinstance(cmap.Colormap('viridis'), cmap.Colormap)
    assert isinstance(cmap.Colormap('crameri:acton'), cmap.Colormap)
    """)
