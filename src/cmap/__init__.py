"""Scientific colormaps for python, without dependencies."""

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Iterator, Mapping

try:
    __version__ = version("cmap")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"


from ._color import HSLA, HSVA, RGBA, RGBA8, Color, ColorLike
from ._colormap import Colormap, ColormapLike, ColorStops

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

        def unique_keys(
            self, prefer_short_names: bool = True, normalized_names: bool = False
        ) -> set[str]:
            """Return names that refer to unique colormap data.

            Parameters
            ----------
            prefer_short_names : bool, optional
                If True (default), short names (without the namespace prefix) will be
                preferred over fully qualified names. In cases where the same short name
                is used in multiple namespaces, they will *all* be referred to by their
                fully qualified (namespaced) name.
            normalized_names : bool, optional
                If True, return the normalized names of the colormaps.  If False
                (default), return the original names of the colormaps (which may include
                spaces and/or capital letters).
            """

        def short_keys(self) -> set[str]:
            """Return a set of available short colormap names, without namespace."""

        def namespaced_keys(self) -> set[str]:
            """Return a set of available short colormap names, with namespace."""

        def resolve(self, name: str) -> str:
            """Return the fully qualified, normalized name of a colormap or alias."""

else:
    from ._catalog import Catalog, CatalogItem

__all__ = [
    "HSLA",
    "HSVA",
    "RGBA",
    "RGBA8",
    "Catalog",
    "CatalogItem",
    "Color",
    "ColorLike",
    "ColorStops",
    "Colormap",
    "ColormapLike",
]
