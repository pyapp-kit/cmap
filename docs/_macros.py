"""Macros for rendering colormaps and colors in the docs.

Loaded by the zensical `macros` extension (see `zensical.toml`). Pages opt in with
`render_macros: true` in their front matter. `_gen_catalog.py` also imports this
module to render the generated catalog pages.
"""

from __future__ import annotations

import base64
import html
import json
import posixpath
from pathlib import Path
from typing import TYPE_CHECKING, Any

import natsort
import numpy as np

from cmap import Colormap
from cmap._color import NAME_TO_RGB

if TYPE_CHECKING:
    from collections.abc import Sequence

DOCS = Path(__file__).parent
CATALOG_INDEX = DOCS / "catalog" / "_data" / "index.json"
CATEGORIES = ("sequential", "diverging", "cyclic", "qualitative", "miscellaneous")


def png_uri(cm: Colormap, width: int = 826, img: np.ndarray | None = None) -> str:
    """Return a base64-encoded PNG data URI for `cm`."""
    data = cm._repr_png_(width=width, height=1, img=img)
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def cmap_page(cm: Colormap) -> str:
    """Return the docs-relative source path of the catalog page for `cm`."""
    name = cm.name.lower().removesuffix("_r")
    return f"catalog/{cm.category}/{name}.md"


def relative(from_page: str, target: str) -> str:
    """Return a link to `target` relative to `from_page` (both docs-relative)."""
    rel = posixpath.relpath(target, posixpath.dirname(from_page) or ".")
    # leading "./" so that names like "bids:viridis.md" aren't parsed as a scheme
    return rel if rel.startswith(".") else f"./{rel}"


def cmap_bar(
    name: str,
    page: str,
    *,
    height: int = 32,
    classes: Sequence[str] = (),
    link: bool = True,
    attrs: str = "",
) -> str:
    """Return single-line HTML for a labeled colorbar of colormap `name`."""
    cm = Colormap(name)
    cls = " ".join(["cmap", *classes])
    img = (
        f'<img src="{png_uri(cm)}" alt="{html.escape(name)} colormap" '
        f'style="height: {height}px" loading="lazy">'
    )
    label = f'<span class="cmap-name">{html.escape(name)}</span>'
    if not link:
        return f'<div class="{cls}"{attrs}>{label}{img}</div>'
    href = relative(page, cmap_page(cm))
    return f'<a class="{cls}" href="{href}"{attrs}>{label}{img}</a>'


def catalog_grid(page: str, category: str | None = None) -> str:
    """Return HTML for the filterable grid of catalog colormaps."""
    if not CATALOG_INDEX.exists():
        raise FileNotFoundError(
            f"{CATALOG_INDEX} not found. Run `python docs/_gen_catalog.py` first."
        )
    entries = natsort.natsorted(
        json.loads(CATALOG_INDEX.read_text()),
        key=lambda e: e["name"],
        alg=natsort.ns.IGNORECASE,
    )
    if category:
        entries = [e for e in entries if e["category"] == category]

    items = []
    for e in entries:
        search = " ".join([e["name"], *e["aliases"]]).lower()
        attrs = (
            f' data-search="{html.escape(search)}"'
            f' data-category="{e["category"]}"'
            f' data-namespace="{e["namespace"]}"'
            f' data-monotonic="{int(e["monotonic"])}"'
        )
        items.append(cmap_bar(e["name"], page, attrs=attrs))

    namespaces = natsort.natsorted({e["namespace"] for e in entries})
    ns_options = "".join(f'<option value="{n}">{n}</option>' for n in namespaces)
    cat_buttons = ""
    if not category:
        cats = [c for c in CATEGORIES if any(e["category"] == c for e in entries)]
        cat_buttons = '<div class="cmap-filter-cats" role="group">' + "".join(
            f'<button type="button" data-category="{c}"'
            f' aria-pressed="{str(c == "all").lower()}">{c.title()}</button>'
            for c in ("all", *cats)
        )
        cat_buttons += "</div>"

    controls = (
        '<div class="cmap-filter">'
        '<input type="search" class="cmap-filter-text" placeholder="Filter by name…"'
        ' aria-label="Filter colormaps by name">'
        '<select class="cmap-filter-ns" aria-label="Filter by source">'
        f'<option value="">All sources</option>{ns_options}</select>'
        '<label class="cmap-filter-mono" title="Lightness (CAM02-UCS J) only ever '
        'increases or only ever decreases (tolerance: 0.5 per step)">'
        '<input type="checkbox"> Monotonic lightness</label>'
        f"{cat_buttons}"
        f'<span class="cmap-filter-count">{len(items)} colormaps</span>'
        "</div>"
    )
    return (
        f'<div class="cmap-catalog" data-search-exclude>{controls}'
        f'<div class="cmap-grid">{"".join(items)}</div>'
        '<p class="cmap-empty" hidden>No colormaps match these filters.</p></div>'
    )


COLORBOX = (
    '<div class="colorbox" style="background-color: {hex}; color: {text}">'
    "<strong>{name}</strong><br><span>{hex}</span><br><span>{rgb}</span></div>"
)


def color_list() -> str:
    """Return HTML for the list of named colors."""
    boxes = []
    for name, c in NAME_TO_RGB.items():
        if (hsl := c.to_hsl()).l == 0.5:
            text = "#000" if hsl.h <= 0.5 else "#FFF"
        else:
            text = "#000" if hsl.l > 0.50 or not c.a else "#FFF"
        boxes.append(
            COLORBOX.format(name=name, hex=c.to_hex(), text=text, rgb=c.rgba_string())
        )
    return f'<div class="colorlist">{"".join(boxes)}</div>'


def define_env(env: Any) -> None:
    """Register macros with the zensical macros extension."""

    def _page() -> str:
        return env.page.path if env.page else ""

    @env.macro
    def cmap(name: str, height: int = 32) -> str:
        return cmap_bar(name, _page(), height=height)

    @env.macro
    def cmap_gray(name: str, height: int = 32) -> str:
        return cmap_bar(name, _page(), height=height, classes=["grayscale"])

    @env.macro
    def cmap_expr(expr: str) -> str:
        cm = Colormap(eval(expr, {"np": np}))  # noqa: S307
        img = f'<img src="{png_uri(cm)}" alt="colormap from {html.escape(expr)}">'
        return f'<div class="cmap cmap-expr">{img}</div>'

    @env.macro
    def cmap_catalog(category: str | None = None) -> str:
        return catalog_grid(_page(), category)

    env.macro(color_list)
