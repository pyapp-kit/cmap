"""Catalog of available colormaps.

This module contains the logic that indexes all of the "record.json" files found
in the data directory.

TODO: this needs to be cleaned up, and documented better.
"""
from __future__ import annotations

import json
import logging
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
        aliases: NotRequired[list[str]]

    class CatalogAlias(TypedDict):
        alias: str
        conflicts: NotRequired[list[str]]

    CatalogDict: TypeAlias = dict[str, CatalogItem]

logger = logging.getLogger("cmap")


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
    aliases: list[str] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}:{self.name}"


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
        namespace = data["namespace"]
        for name, v in data["colormaps"].items():
            namespaced = f"{namespace}:{name}"

            # if the key "alias" exists, this is a CatalogAlias.
            # We just add it to the catalog under both the namespaced name
            # and the short name.  The Catalog._load method will handle the resolution
            # of the alias.
            if "alias" in v:
                v = cast("CatalogAlias", v)
                if ":" not in v["alias"]:  # pragma: no cover
                    raise ValueError(f"{namespaced!r} alias is not namespaced")
                CATALOG[namespaced] = v
                CATALOG[name] = v  # FIXME
                continue

            # otherwise we have a CatalogItem
            v = cast("CatalogItem", v)

            # here we add any global keys to the colormap that are not already there.
            for k in ("license", "namespace", "source", "authors", "category"):
                if k in data:
                    v.setdefault(k, data[k])

            # add the fully namespaced colormap to the catalog
            CATALOG[namespaced] = v

            # if the short name is not already in the catalog, add it as a pointer
            # to the fully namespaced colormap.
            if name not in CATALOG:
                CATALOG[name] = {"alias": namespaced, "conflicts": []}
            else:
                # if the short name is already in the catalog, we have a conflict.
                # add the fully namespaced name to the conflicts list.
                entry = cast("CatalogAlias", CATALOG[name])
                entry.setdefault("conflicts", []).append(namespaced)

            # lastly, the `aliases` key of a colormap refers to aliases within the
            # namespace.  These are keys that *must* be accessed using the fullly
            # namespaced name (with a colon).  We add these to the catalog as well
            # so that they can be
            for alias in v.get("aliases", []):
                if ":" in alias:  # pragma: no cover
                    raise ValueError(
                        f"internal alias {alias!r} in namespace {namespace} "
                        "should not have colon."
                    )
                CATALOG[f"{namespace}:{alias}"] = {"alias": namespaced}


_populate_catalog()
_CATALOG_LOWER = {_norm_name(k): v for k, v in CATALOG.items()}
_ALIASES: dict[str, list[str]] = {}
for k, v in _CATALOG_LOWER.items():
    if alias := v.get("alias"):
        _ALIASES.setdefault(_norm_name(alias), []).append(k)  # type: ignore


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
                logger.warning(
                    f"WARNING: The name {key!r} is an alias for {namespaced!r}, "
                    f"but is also available as: {', '.join(conflicts)!r}.\nTo "
                    "silence this warning, use a fully namespaced name.",
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
        _item["aliases"] = _ALIASES.get(key, [])
        return LoadedCatalogItem(name=key.split(":", 1)[-1], **_item)


catalog = Catalog()
