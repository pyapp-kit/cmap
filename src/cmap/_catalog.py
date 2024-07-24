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
from typing import (
    TYPE_CHECKING,
    Any,
    Container,
    Iterable,
    Iterator,
    Literal,
    Mapping,
    cast,
)

import cmap.data

if TYPE_CHECKING:
    from _typeshed import FileDescriptorOrPath
    from typing_extensions import NotRequired, Required, TypeAlias, TypedDict

    from ._colormap import ColorStopsLike, Interpolation

    Category: TypeAlias = Literal[
        "sequential", "diverging", "cyclic", "qualitative", "miscellaneous"
    ]

    class UnloadedCatalogItem(TypedDict):
        data: str
        category: Category
        tags: NotRequired[list[str]]
        interpolation: NotRequired[bool]
        info: NotRequired[str]
        aliases: NotRequired[list[str]]
        over: NotRequired[str]
        under: NotRequired[str]
        bad: NotRequired[str]
        authors: NotRequired[list[str]]
        license: NotRequired[str]

    class UnloadedCatalogAlias(TypedDict):
        alias: str
        conflicts: NotRequired[list[str]]

    CatalogDict: TypeAlias = dict[str, UnloadedCatalogItem | UnloadedCatalogAlias]

    class RecordItem(TypedDict):
        """Json schema for a single colormap record file."""

        namespace: Required[str]
        colormaps: Required[CatalogDict]
        # globals that are used if missing on colormap values
        license: str
        source: str
        authors: list[str]
        category: Category


logger = logging.getLogger("cmap")
RECORD_PATTERN = "record.json"
DATA_ROOT = Path(cmap.data.__file__).parent
NAMESPACE_DELIMITER = ":"


@dataclass
class CatalogItem:
    """A loaded catalog item.

    Attributes
    ----------
    data: ColorStopsLike
        Any object that can be passed to `Colormap` to create a colormap.
        https://cmap-docs.readthedocs.io/en/latest/colormaps/#colormaplike-objects
    name: str
        The (short) name of the colormap, e.g. "viridis".
    category: str
        The category of the colormap. One of {"sequential", "diverging", "cyclic",
        "qualitative", "miscellaneous"}.
    license: str
        The license of the colormap.
    source: str
        The source of the colormap (usually a URL).
    info: str
        A description of the colormap. Will be displayed on the colormap page in the
        documentation.
    namespace: str
        The namespace of the colormap. This is a cmap-specific namespace for organizing
        colormaps into collections.  (e.g. "matplotlib", "cmocean", "colorcet", etc.)
    authors: list[str]
        A list of authors of the colormap.
    interpolation: bool | Interpolation
        The interpolation method to use when sampling the colormap.  One of
        {False, True, "linear", "nearest"}, where False is equivalent to "nearest"
        and True is equivalent to "linear".  If not provided, defaults to "linear".
    tags: list[str]
        A list of tags for the colormap. These are displayed in the documentation.
    aliases: list[str]
        A list of aliases for the colormap. These are alternative names that can be
        used to access the colormap. Currently, they must be accessed using the
        fully qualified name (`namespace:alias`).
    qualified_name: str
        The fully qualified name of the colormap, e.g. "matplotlib:viridis".
    under: str | None
        The color to use for under-range values.
    over: str | None
        The color to use for over-range values.
    bad: str | None
        The color to use for bad values.
    """

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
    under: str | None = None
    over: str | None = None
    bad: str | None = None

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}{NAMESPACE_DELIMITER}{self.name}"


def _build_catalog(records: Iterable[FileDescriptorOrPath]) -> CatalogDict:
    """Populate the catalog with data from the data directory."""
    # FIXME: if a new collection is added, it has the potential to break
    # existing code that uses the old name without a namespace.  One way
    # to avoid this would be to explicitly list the collections here.
    # but then new collections would need to be added here to be
    # available.
    ctlg: CatalogDict = {}

    for record_file in records:
        with open(record_file) as f:
            data = cast("RecordItem", json.load(f))
        namespace = data["namespace"]
        for name, v in data["colormaps"].items():
            if NAMESPACE_DELIMITER in name:  # pragma: no cover
                raise ValueError(f"colormap name {name!r} should not have colon.")
            if NAMESPACE_DELIMITER in namespace:  # pragma: no cover
                raise ValueError(f"namespace {namespace!r} should not have colon.")

            namespaced = f"{namespace}{NAMESPACE_DELIMITER}{name}"

            # if the key "alias" exists, this is a UnloadedCatalogAlias.
            # We just add it to the catalog under both the namespaced name
            # and the short name.  The Catalog._load method will handle the resolution
            # of the alias.
            if "alias" in v:
                v = cast("UnloadedCatalogAlias", v)
                if NAMESPACE_DELIMITER not in v["alias"]:  # pragma: no cover
                    raise ValueError(f"{namespaced!r} alias is not namespaced")
                ctlg[namespaced] = v
                ctlg[name] = v  # FIXME
                continue

            # otherwise we have a CatalogItem
            v = cast("UnloadedCatalogItem", v)

            # here we add any global keys to the colormap that are not already there.
            for k in ("license", "namespace", "source", "authors", "category"):
                if k in data:
                    v.setdefault(k, data[k])  # type: ignore [misc,literal-required]

            # add the fully namespaced colormap to the catalog
            ctlg[namespaced] = v

            # if the short name is not already in the catalog, add it as a pointer
            # to the fully namespaced colormap.
            if name not in ctlg:
                ctlg[name] = {"alias": namespaced, "conflicts": []}
            else:
                # if the short name is already in the catalog, we have a conflict.
                # add the fully namespaced name to the conflicts list.
                entry = cast("UnloadedCatalogAlias", ctlg[name])
                entry.setdefault("conflicts", []).append(namespaced)

            # lastly, the `aliases` key of a colormap refers to aliases within the
            # namespace.  These are keys that *must* be accessed using the fully
            # namespaced name (with a colon).  We add these to the catalog as well
            # so that they can be
            for alias in v.get("aliases", []):
                if NAMESPACE_DELIMITER in alias:  # pragma: no cover
                    raise ValueError(
                        f"internal alias {alias!r} in namespace {namespace} "
                        "should not have colon."
                    )
                ctlg[f"{namespace}{NAMESPACE_DELIMITER}{alias}"] = {"alias": namespaced}

    return ctlg


class Catalog(Mapping[str, "CatalogItem"]):
    """Catalog of available colormaps.

    Parameters
    ----------
    root : Path, optional
        Path to the root of the data directory, by default uses the `cmap.data` folder.
    record_pattern : str, optional
        Glob pattern to use to find record files, by default "record.json".
    """

    def __init__(
        self, data_root: Path = DATA_ROOT, record_pattern: str = RECORD_PATTERN
    ) -> None:
        self._data_root = data_root
        self._record_pattern = record_pattern

        # a cache of loaded CatalogItem
        self._loaded: dict[str, CatalogItem] = {}

        # _data is a mapping of ALL possible (normalized) names to colormap data.
        # this includes both short names and namespaced names.
        self._data: CatalogDict = {}
        # original names maps the original name as it appeared in the record to the
        # normalized name in _data
        self._original_names: dict[str, str] = {}
        # _aliases maps short names to fully namespaced names
        self._aliases: dict[str, str] = {}
        # _rev_aliases maps fully qualified names to a list of aliases
        self._rev_aliases: dict[str, list[str]] = {}

        for name, data in _build_catalog(
            sorted(data_root.rglob(record_pattern))
        ).items():
            normed_name = self._norm_name(name)
            self._original_names[name] = normed_name
            self._data[normed_name] = data
            if alias := data.get("alias"):
                self._aliases[normed_name] = cast(str, alias)
                self._rev_aliases.setdefault(self._norm_name(alias), []).append(
                    normed_name
                )

    def unique_keys(
        self,
        prefer_short_names: bool = True,
        normalized_names: bool = False,
        categories: Container[Category] = (),
        interpolation: Interpolation | None = None,
    ) -> set[str]:
        """Return names that refer to unique colormap data.

        Parameters
        ----------
        prefer_short_names : bool, optional
            If True (default), short names (without the namespace prefix) will be
            preferred over fully qualified names. In cases where the same short name is
            used in multiple namespaces, they will *all* be referred to by their fully
            qualified (namespaced) name.
        normalized_names : bool, optional
            If True, return the normalized names of the colormaps.  If False (default),
            return the original names of the colormaps (which may include spaces and/or
            capital letters).
        categories : Container[Category], optional
            If provided, only return colormaps in the given categories.
        interpolation : Interpolation, optional
            If provided, only return colormaps with the given interpolation method.

        Returns
        -------
        set[str]
            A set of unique colormap names that can be used to access the colormap data.
        """
        keys: set[str] = set()
        for original_name, normed_name in self._original_names.items():
            data = self._data[normed_name]
            if "alias" in data:
                continue
            if categories and data["category"] not in categories:
                continue
            if interpolation is not None:
                interp = data.get("interpolation", "linear")
                if isinstance(interp, bool):
                    interp = "linear" if interp else "nearest"
                if interp != interpolation:
                    continue

            if prefer_short_names:
                short_name = normed_name.split(NAMESPACE_DELIMITER, 1)[-1]
                data2 = self._data[short_name]
                if not data2.get("conflicts") and data2.get("alias") == original_name:
                    keys.add(
                        short_name
                        if normalized_names
                        else original_name.split(NAMESPACE_DELIMITER, 1)[-1]
                    )
                    continue
            keys.add(normed_name if normalized_names else original_name)
        return keys

    def short_keys(self) -> set[str]:
        """Return a set of available short colormap names, without namespace."""
        return {n for n in self._original_names if NAMESPACE_DELIMITER not in n}

    def namespaced_keys(self) -> set[str]:
        """Return a set of available short colormap names, with namespace."""
        return {n for n in self._original_names if NAMESPACE_DELIMITER in n}

    def resolve(self, name: str) -> str:
        """Return the fully qualified, normalized name of a colormap or alias."""
        nn = self._norm_name(name)
        if nn in self._aliases:
            return self._aliases[nn]
        if nn in self._data:
            return nn
        raise KeyError(f"Could not find colormap with name {name!r}.")

    def _ipython_key_completions_(self) -> list[str]:
        """Support ipython tab completion."""
        return list(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._original_names)

    def __len__(self) -> int:
        return len(self._original_names)

    def __getitem__(self, name: str) -> CatalogItem:
        if name not in self._loaded:
            if (key := self._norm_name(name)) not in self._data:
                # TODO: print a list of available colormaps or something
                if name != key:  # pragma: no cover
                    raise ValueError(f"Colormap {name!r} (or {key!r}) not found.")
                raise ValueError(f"Colormap {name!r} not found.")

            self._loaded[name] = self._load(key)
            if key != name:
                # cache the requested name as well so we don't need to renormalize
                self._loaded[key] = self._loaded[name]
        return self._loaded[name]

    def _load(self, normed_key: str) -> CatalogItem:
        """Get the data for a named colormap."""
        item = self._data[normed_key]
        # aliases are just pointers to other colormaps
        if "alias" in item:
            item = cast("UnloadedCatalogAlias", item)
            namespaced = item["alias"]
            if conflicts := item.get("conflicts"):
                logger.warning(
                    f"WARNING: The name {normed_key!r} is an alias for {namespaced!r}, "
                    f"but is also available as: {', '.join(conflicts)!r}.\nTo "
                    "silence this warning, use a fully namespaced name.",
                )
            return self[namespaced]

        _item = cast("UnloadedCatalogItem", item.copy())
        # if a string, it is a module:attribute reference to a ColormapLike object
        # load it here.
        if isinstance(_item["data"], str):
            module, attr = _item["data"].rsplit(NAMESPACE_DELIMITER, 1)
            # not encouraged... but significantly faster than importlib
            # well tested on internal data though
            mod = __import__(module, fromlist=[attr])
            _item["data"] = getattr(mod, attr)
        _item["aliases"] = self._rev_aliases.get(normed_key, [])
        return CatalogItem(name=normed_key.split(NAMESPACE_DELIMITER, 1)[-1], **_item)

    @staticmethod
    def _norm_name(name: Any) -> str:
        return str(name).lower().replace(" ", "_").replace("-", "_")
