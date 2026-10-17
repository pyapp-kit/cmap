"""Generate the colormap catalog pages and data.

This must run before `zensical build` / `zensical serve`:

    uv run --group docs python docs/_gen_catalog.py

Outputs (all git-ignored, under `docs/catalog/`):

- `<category>/index.md`: one page per category, with a grid of its colormaps.
- `<category>/<name>.md`: one page per (non-alias) colormap.
- `<category>/<alias>/index.html`: redirects from aliases to the canonical page.
- `_data/index.json`: metadata used by the catalog grid and compare page.
- `_data/<name>.json`: lightness/hue/etc data for each colormap and CVD type.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

import jinja2
import natsort
import numpy as np

from cmap import Colormap
from cmap._util import report_cvds

sys.path.insert(0, str(Path(__file__).parent))
from _macros import CATEGORIES, cmap_bar, cmap_page, relative

if TYPE_CHECKING:
    from cmap._catalog import CatalogItem

DOCS = Path(__file__).parent
OUT = DOCS / "catalog"

LICENSE_URL = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "Apache-2.0": "https://www.apache.org/licenses/LICENSE-2.0",
    "MIT": "https://opensource.org/licenses/MIT",
    "BSD-3-Clause": "https://opensource.org/licenses/BSD-3-Clause",
    "BSD-2-Clause": "https://opensource.org/licenses/BSD-2-Clause",
    "PSF": "https://opensource.org/licenses/Python-2.0",
}
# extra test image (rendered client-side, see cmap.js) per category
SQUARE_TEST_IMAGES = {
    "cyclic": {
        "kind": "circlesineramp",
        "label": "circular sine ramp",
        "title": "Circular sine ramp test image (Kovesi): the sine wave should be "
        "equally visible all the way around, with no seam on the right",
    },
    "diverging": {
        "kind": "peaks",
        "label": "peaks",
        "title": "MATLAB's peaks surface, scaled so that 0 is the colormap's midpoint",
    },
}
CVD_LABELS = {
    "normal": "Normal vision",
    "protan": "Protanopia",
    "deutan": "Deuteranopia",
    "tritan": "Tritanopia",
}
# (key in report, key in output json, decimals)
REPORT_FIELDS = (
    ("J", "J", 1),
    ("lightness_derivs", "dJ", 0),
    ("hue", "hue", 0),
    ("saturation", "saturation", 1),
    ("chroma", "chroma", 1),
)
MAX_SAMPLES = 256
# max per-step decrease in J' for a colormap to still count as "monotonic"
MONOTONIC_TOL = 0.5
# absolute links to catalog pages in `info` strings, e.g. "/catalog/sequential/rdbu/"
CATALOG_LINK = re.compile(r"\]\(/catalog/[^/]+/([^/)]+)/?\)")

PAGE = jinja2.Template(
    """\
---
title: {{ name | tojson }}
description: {{ description | tojson }}
---

# {{ name }}

{% if aliases %}**Aliases**: {{ aliases }}
{% endif %}
{{ info }}

| category | license | authors | source |
| --- | --- | --- | --- |
| [{{ category | title }}](index.md) | {{ license }} | {{ authors }} | {{ source }} |

<div class="cmap-snippets" data-search-exclude markdown>

=== "cmap"

    ```python
    from cmap import Colormap

    cm = Colormap("{{ name }}")  # case insensitive
    ```

=== "matplotlib"

    ```python
    import matplotlib.pyplot as plt
    from cmap import Colormap

    plt.imshow(data, cmap=Colormap("{{ name }}").to_mpl())
    ```

=== "napari"

    ```python
    import napari
    from cmap import Colormap

    napari.view_image(data, colormap=Colormap("{{ name }}").to_napari())
    ```

=== "CSS"

    ```css
    {{ css | indent(4) }}
    ```

</div>

<div class="cmap-detail" data-cmap-name="{{ name }}" data-json="{{ data_url }}">
{{ bar }}
{{ gray }}
<div class="cmap-test-images">
<canvas class="cmap-sineramp" data-test-image="sineramp" width="826" height="96" title="Sine ramp test image (Kovesi): the sine wave at the top should be equally visible across the whole range" aria-label="{{ name }} applied to a sine ramp test image"></canvas>
{% if square %}<canvas class="cmap-test-square" data-test-image="{{ square.kind }}" width="320" height="320" title="{{ square.title }}" aria-label="{{ name }} applied to the {{ square.label }} test image"></canvas>
{% endif %}</div>
<fieldset class="cmap-cvd" role="radiogroup" aria-label="Simulate color vision deficiency">
{% for key, label in cvd_labels.items() %}<label><input type="radio" name="cvd" value="{{ key }}"{% if loop.first %} checked{% endif %}><span>{{ label }}</span></label>
{% endfor %}</fieldset>
</div>

[:lucide-git-compare: Compare with other colormaps](../../compare.md?cmaps={{ name | urlencode }}){ .md-button }

## Perceptual lightness { data-search-exclude }

<div class="cmap-chart-wrap"><canvas class="cmap-chart" data-chart="lightness" data-cmap-name="{{ name }}"></canvas></div>

<p class="cmap-chart-caption">
Lightness (J&prime;) measured in
<a href="https://onlinelibrary.wiley.com/doi/10.1002/col.20227">CAM02 Uniform Color Space (CAM02-UCS)</a>
</p>

## RGB components { data-search-exclude }

<div class="cmap-chart-wrap"><canvas class="cmap-chart" data-chart="rgb" data-cmap-name="{{ name }}"></canvas></div>

## Hue & saturation { data-search-exclude }

<div class="cmap-chart-wrap"><canvas class="cmap-chart" data-chart="hsl" data-cmap-name="{{ name }}"></canvas></div>

---

<nav class="cmap-pager" markdown>
{% if prev %}[:lucide-arrow-left: {{ prev.name }}]({{ prev.href }}){% endif %}
{% if next %}[{{ next.name }} :lucide-arrow-right:]({{ next.href }}){% endif %}
</nav>
"""
)

CATEGORY_PAGE = """\
---
title: {title} colormaps
render_macros: true
---

# {title} colormaps

{{{{ cmap_catalog("{category}") }}}}
"""

REDIRECT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="{url}">
<meta name="robots" content="noindex">
<script>location.replace("{url}" + location.hash)</script>
<meta http-equiv="refresh" content="0; url={url}">
</head>
<body>Redirecting to <a href="{url}">{url}</a>…</body>
</html>
"""


def _report_data(cm: Colormap) -> dict[str, dict[str, Any]]:
    """Return the (trimmed) chart data for each CVD type."""
    out = {}
    for cvd, report in report_cvds(cm).items():
        n = len(report["color"])
        idx = np.linspace(0, n - 1, min(n, MAX_SAMPLES)).round().astype(int)
        d: dict[str, Any] = {"color": [report["color"][i][1:] for i in idx]}
        for src, dst, decimals in REPORT_FIELDS:
            vals = np.around(np.asarray(report[src], dtype=float)[idx], decimals)
            # NaN isn't valid JSON (e.g. hue of grays)
            d[dst] = [
                (int(v) if decimals == 0 else float(v)) if np.isfinite(v) else None
                for v in vals
            ]
        out[cvd] = d
    return out


def _is_monotonic(lightness: list[float]) -> bool:
    diff = np.diff(lightness)
    return bool(np.all(diff >= -MONOTONIC_TOL) or np.all(diff <= MONOTONIC_TOL))


def _fix_info_links(info: str, page: str) -> str:
    """Make absolute catalog links in `info` relative to `page`."""

    def _sub(m: re.Match) -> str:
        return f"]({relative(page, cmap_page(Colormap(m[1])))})"

    return CATALOG_LINK.sub(_sub, info)


def _md_link(url: str) -> str:
    return f"[{url}]({url})" if url.startswith("http") else f"`{url}`"


def _iter_items() -> list[tuple[str, CatalogItem]]:
    catalog = Colormap.catalog()
    items = []
    for name in natsort.natsorted(catalog, alg=natsort.ns.IGNORECASE):
        if ":" not in name:
            continue
        info = catalog[name]
        # FIXME: not a great way to determine aliases...
        # prone to false positives if normalization is not perfect/consistent
        if info.qualified_name.lower() != name.lower():
            continue
        items.append((name, info))
    return items


class _Writer:
    """Write files under `OUT`, skipping unchanged ones (keeps `zensical serve` happy).

    Call `prune()` at the end to remove previously generated files that are stale.
    """

    def __init__(self) -> None:
        self.written: set[Path] = set()

    def __call__(self, rel: str, content: str) -> None:
        path = OUT / rel
        self.written.add(path)
        if path.exists() and path.read_text(encoding="utf-8") == content:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def prune(self) -> None:
        for d in (*CATEGORIES, "_data"):
            for path in sorted((OUT / d).rglob("*"), reverse=True):
                if path.is_file() and path not in self.written:
                    path.unlink()
                elif path.is_dir() and not any(path.iterdir()):
                    path.rmdir()


def _write_redirects(write: _Writer) -> None:
    """Write redirect pages for every alias in the catalog."""
    for name, details in Colormap.catalog()._data.items():
        if "alias" not in details:
            continue
        real = Colormap(details["alias"])  # type: ignore[typeddict-item]
        # relative to the redirect page's own url (".../<alias>/")
        url = "../" + Path(cmap_page(real)).stem + "/"
        alias_dir = name.replace(":", "-")
        write(f"{real.category}/{alias_dir}/index.html", REDIRECT.format(url=url))


def _render_page(
    name: str, info: CatalogItem, prev: str | None, next_: str | None
) -> str:
    cm = Colormap(name)
    page = cmap_page(cm)

    def _link(other: str | None) -> dict | None:
        if other is None:
            return None
        return {"name": other, "href": relative(page, cmap_page(Colormap(other)))}

    license_ = info.license
    if license_ in LICENSE_URL:
        license_ = f"[{license_}]({LICENSE_URL[license_]})"
    return PAGE.render(
        name=name,
        description=f"{name}: a {info.category} colormap from {info.namespace}.",
        aliases=", ".join(f"`{a}`" for a in info.aliases if a != info.name),
        info=_fix_info_links(info.info, page),
        category=info.category,
        license=license_,
        authors=", ".join(info.authors),
        source=_md_link(info.source),
        css=cm.to_css(max_stops=32, as_hex=True).strip(),
        bar=cmap_bar(name, page, height=40, link=False),
        gray=cmap_bar(name, page, height=30, link=False, classes=["grayscale"]),
        cvd_labels=CVD_LABELS,
        square=SQUARE_TEST_IMAGES.get(info.category),
        data_url=f"../../_data/{quote(Path(page).stem)}.json",
        prev=_link(prev),
        next=_link(next_),
    )


def build() -> None:
    write = _Writer()
    by_category: dict[str, list[tuple[str, CatalogItem]]] = {}
    for name, info in _iter_items():
        by_category.setdefault(info.category, []).append((name, info))

    # every name (short or namespaced) that resolves to a given colormap
    aliases: dict[str, set[str]] = {}
    for alias, details in Colormap.catalog()._data.items():
        if target := details.get("alias"):
            aliases.setdefault(str(target).lower(), set()).add(alias)

    index = []
    for category, cat_items in by_category.items():
        title = category.title()
        write(
            f"{category}/index.md", CATEGORY_PAGE.format(title=title, category=category)
        )
        names = [n for n, _ in cat_items]
        for i, (name, info) in enumerate(cat_items):
            page = cmap_page(Colormap(name)).removeprefix("catalog/")
            data = _report_data(Colormap(name))
            index.append(
                {
                    "name": name,
                    "category": category,
                    "namespace": info.namespace,
                    "aliases": natsort.natsorted(aliases.get(name.lower(), ())),
                    "monotonic": _is_monotonic(data["normal"]["J"]),
                    "path": page.removesuffix(".md"),
                }
            )
            write(
                f"_data/{Path(page).stem}.json", json.dumps(data, separators=(",", ":"))
            )
            prev = names[i - 1] if i > 0 else None
            next_ = names[i + 1] if i + 1 < len(names) else None
            write(page, _render_page(name, info, prev, next_))

    write("_data/index.json", json.dumps(index, separators=(",", ":")))
    _write_redirects(write)
    write.prune()
    print(f"Generated {len(index)} colormap pages in {OUT}")


if __name__ == "__main__":
    build()
