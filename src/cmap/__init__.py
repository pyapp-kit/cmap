"""Scientific colormaps for python, without dependencies."""
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Iterator, Mapping

try:
    __version__ = version("cmap")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"


from ._color import HSLA, HSVA, RGBA, RGBA8, Color
from ._colormap import Colormap

if TYPE_CHECKING:
    from ._catalog import CatalogItem

    class Catalog(Mapping[str, CatalogItem]):
        """Catalog of available colormaps."""

        def __getitem__(self, name: str) -> CatalogItem:
            """Get a catalog item by name."""

        def __iter__(self) -> Iterator[str]:
            """Iterate over available colormap keys."""

        def __len__(self) -> int:
            """Return the number of available colormap keys.

            Note: this is greater than the number of colormaps, as each colormap
            may have multiple aliases.
            """

else:
    from ._catalog import Catalog, CatalogItem

__all__ = [
    "Color",
    "Colormap",
    "CatalogItem",
    "Catalog",
    "HSLA",
    "HSVA",
    "RGBA",
    "RGBA8",
]
