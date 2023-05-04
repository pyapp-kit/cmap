from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Literal, Mapping, cast

import cmap.data

if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypeAlias, TypedDict

    from ._colormap import ColorStopsLike, Interpolation

    Category: TypeAlias = Literal[
        "sequential", "diverging", "cyclic", "qualitative", "miscellaneous"
    ]

    class CatalogItem(TypedDict):
        data: str
        category: Category
        tags: NotRequired[list[str]]
        interpolation: NotRequired[bool]
        info: NotRequired[str]

    class CatalogAlias(TypedDict):
        alias: str
        conflicts: NotRequired[list[str]]

    CatalogDict: TypeAlias = dict[str, CatalogItem]


def _norm_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


@dataclass
class LoadedCatalogItem:
    data: ColorStopsLike
    name: str
    category: Category
    license: str = "UNKNOWN"
    source: str = ""
    info: str = ""
    namespace: str = ""
    authors: list[str] = field(default_factory=list)
    interpolation: bool | Interpolation = "linear"
    tags: list[str] = field(default_factory=list)


CATALOG: dict[str, CatalogItem | CatalogAlias] = {}


def _populate_catalog() -> None:
    """Populate the catalog with data from the data directory."""
    # FIXME: if a new collection is added, it has the potential to break
    # existing code that uses the old name without a namespace.  One way
    # to avoid this would be to explicitly list the collections here.
    # but then new collections would need to be added here to be
    # available.
    for r in sorted(Path(cmap.data.__file__).parent.rglob("record.json")):
        with open(r) as f:
            data = json.load(f)
        for name, v in data["colormaps"].items():
            v = cast("CatalogItem | CatalogAlias", v)
            namespaced = f"{data['namespace']}:{name}"
            if "alias" in v:
                if ":" not in v["alias"]:  # pragma: no cover
                    raise ValueError(f"{namespaced!r} alias is not namespaced")
                CATALOG[namespaced] = v
                CATALOG[name] = v  # FIXME
                continue

            for k in ("license", "namespace", "source", "authors", "category"):
                if k in data:
                    v.setdefault(k, data[k])

            CATALOG[namespaced] = v

            if name not in CATALOG:
                CATALOG[name] = {"alias": namespaced, "conflicts": []}
            else:
                d_ = cast("CatalogAlias", CATALOG[name])
                d_.setdefault("conflicts", []).append(namespaced)


_populate_catalog()
_CATALOG_LOWER = {_norm_name(k): v for k, v in CATALOG.items()}


class Catalog(Mapping[str, "LoadedCatalogItem"]):
    _loaded: dict[str, LoadedCatalogItem] = {}

    def __iter__(self) -> Iterator[str]:
        return iter(CATALOG)

    def __len__(self) -> int:
        return len(CATALOG)

    def __getitem__(self, name: str) -> LoadedCatalogItem:
        if name not in self._loaded:
            if (key := _norm_name(name)) not in _CATALOG_LOWER:
                # TODO: print a list of available colormaps or something
                if name != key:  # pragma: no cover
                    raise ValueError(f"Colormap {name!r} (or {key!r}) not found.")
                raise ValueError(f"Colormap {name!r} not found.")

            self._loaded[name] = self._load(key)
            if key != name:
                # cache the requested name as well so we don't need to renormalize
                self._loaded[key] = self._loaded[name]
        return self._loaded[name]

    def _load(self, key: str) -> LoadedCatalogItem:
        """Get the data for a named colormap."""
        item = _CATALOG_LOWER[key]
        # aliases are just pointers to other colormaps
        if "alias" in item:
            item = cast("CatalogAlias", item)
            namespaced = item["alias"]
            if conflicts := item.get("conflicts"):
                warnings.warn(
                    f"The name {key!r} is an alias for {namespaced!r}, but is also "
                    f"available as: {', '.join(conflicts)!r}. To silence this "
                    "warning, use a fully namespaced name.",
                    stacklevel=2,
                )
            return self[namespaced]

        _item = cast("CatalogItem", item.copy())
        # if a string, it is a module:attribute reference to a ColormapLike object
        # load it here.
        if isinstance(_item["data"], str):
            module, attr = _item["data"].rsplit(":", 1)
            # not encouraged... but significantly faster than importlib
            # well tested on internal data though
            mod = __import__(module, fromlist=[attr])
            _item["data"] = getattr(mod, attr)
        return LoadedCatalogItem(name=key.split(":", 1)[-1], **_item)


catalog = Catalog()
