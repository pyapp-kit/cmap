import base64
import re
import sys
from functools import partial
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from cmap import Colormap, _util
from cmap._catalog import CATALOG
from cmap._color import NAME_TO_RGB

# the template for a single colormap
CMAP_DIV = """
<div class="cmap {class_list}" id="cmap-{name}">
    <div class="cmap-name">{name}</div>
    {img}
</div>
"""
CMAP_LINK = '<a href="{url}">' + CMAP_DIV + "</a>"
DEV_MODE = "serve" in sys.argv
SINERAMP = _util.sineramp((96, 512))[:, ::-1]


class DocCmap(Colormap):
    def to_img_tag(
        self,
        height: str = "32px",
        width: str = "100%",
        img: np.ndarray | None = None,
    ) -> str:
        """Return a base64-encoded <img> tag for the given colormap.

        <img style="height: 32px" width="100%" src="data:image/png;base64, ...">
        """
        data = base64.b64encode(self._png_bytes(img)).decode("ascii")
        return (
            f'<img style="height: {height}" width="{width}" src="data:image/png;base64, '
            f'{data}" alt="{self.name} colormap" />'
        )

    def _png_bytes(self, img: np.ndarray | None = None) -> bytes:
        import io

        from PIL import Image

        if img is None:
            img = np.linspace(0, 1, 256)[None]
        ary = (self(img) * 255).astype("uint8")
        with io.BytesIO() as fp:
            Image.fromarray(ary).save(fp, format="png")
            return fp.getvalue()

    def url(self) -> str:
        return f'/catalog/{self.category}/{self.name.lower().replace("_r", "")}/'


def _cmap_div(match: re.Match | str, class_list: Sequence[str] = ()) -> str:
    """Convert a `cmap` tag to a div with the colormap.

    {{ cmap: name }} -> <div class="cmap">
    """
    map_name = match if isinstance(match, str) else match[1].strip()
    cm = DocCmap(map_name)
    height = (match[2] if isinstance(match, re.Match) else None) or 32
    img = cm.to_img_tag(height=f"{height}px")
    return CMAP_LINK.format(
        name=map_name, img=img, class_list=" ".join(class_list), url=cm.url()
    )


def _cmap_expr(match: re.Match) -> str:
    """Convert a `cmap_expr` tag to a div with the colormap.

    {{ cmap_expr: {0: 'blue', 0.5: 'yellow', 1: 'red'} }} -> <div class="cmap">...
    """
    cm = DocCmap(eval(match[1].strip()))
    return CMAP_DIV.format(name="", img=cm.to_img_tag(), class_list="cmap-expr")


def _cmap_sineramp(match: re.Match) -> str:
    """Convert a `cmap_sineramp` tag to an img element with sineramp applied.

    {{ cmap_sineramp: viridis }} -> <img class="cmap">...
    """
    # if DEV_MODE:
    # return "[sineramp slow -- disabled in `mkdocs serve`]"

    map_name = match[1].strip()
    return DocCmap(map_name).to_img_tag(f"{SINERAMP.shape[0]}px", img=SINERAMP)


def _cmap_catalog() -> str:
    """Return the HTML for the colormap catalog page.

    this works in conjunction with the `javascripts/extra.js` script.
    """
    categories = set()
    lines = []
    for cmap_name, details in sorted(CATALOG.items(), key=lambda x: x[0].lower()):
        if "alias" in details:
            continue
        category = details.get("category") or "Uncategorized"
        categories.add(category)
        classes = ["filterDiv"] + [category.lower()]
        lines.append(_cmap_div(cmap_name, classes))

    btns = [
        '<div id="cmapFilterButtons">',
        """<button class="btn active" onclick="filterSelection('all')">All</button>""",
    ]
    btns.extend(
        f'<button class="btn" onclick="filterSelection({c.lower()!r})">{c}</button>'
        for c in sorted(categories)
    )
    btns.append("</div>")
    lines = btns + lines

    return "\n".join(lines)


COLORBOX = """<div class="colorbox" style="background-color: {hex}; color: {text_color}">
    <strong class="colornamespan">{name}</strong><br />
    <span class="colorhexspan">{hex}</span><br />
    <span class="colortuple">{rgb}</span><br />
</div>
"""


def _color_list() -> str:
    """Return the HTML for the color list page."""
    colors = []
    for name, c in NAME_TO_RGB.items():
        if (hsl := c.to_hsl()).l == 0.5:
            text_color = "#000" if hsl.h <= 0.5 else "#FFF"
        else:
            text_color = "#000" if hsl.l > 0.50 or not c.a else "#FFF"
        cbox = COLORBOX.format(
            name=name,
            hex=c.to_hex(),
            text_color=text_color,
            rgb=c.rgba_string(),
        )
        colors.append(cbox)
    return '<div class="colorlist">{}</div>'.format("\n".join(colors))


# -----------------------------------------------------------------------------
# mkdocs hooks
# -----------------------------------------------------------------------------

# markdown tag for a single colormap: {{ cmap: name }}
CSS_CMAP = re.compile(r"{{\s?cmap:\s?([^}^\s]+)\s?(\d+)?\s?}}")
CSS_CMAP_GRAY = re.compile(r"{{\s?cmap_gray:\s?([^}^\s]+)\s?(\d+)?\s?}}")
CMAP_SINERAMP = re.compile(r"{{\s?cmap_sineramp:\s?([^}]+)\s?}}")
CMAP_EXPR = re.compile(r"{{\s?cmap_expr:\s(.+)\s}}")
CMAP_CATALOG = r"{{ CMAP_CATALOG }}"
COLOR_LIST = r"{{ COLOR_LIST }}"


def on_page_content(html: str, **kwargs: Any) -> str:
    html = CSS_CMAP.sub(_cmap_div, html)
    html = CSS_CMAP_GRAY.sub(partial(_cmap_div, class_list=["grayscale"]), html)
    html = CMAP_EXPR.sub(_cmap_expr, html)
    html = CMAP_SINERAMP.sub(_cmap_sineramp, html)
    if CMAP_CATALOG in html:
        html = html.replace(CMAP_CATALOG, _cmap_catalog())
    if COLOR_LIST in html:
        html = html.replace(COLOR_LIST, _color_list())
    return html


REDIRECT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Redirecting...</title>
    <link rel="canonical" href="{url}">
    <meta name="robots" content="noindex">
    <script>
    var anchor=window.location.hash.substr(1);location.href="{url}"+(anchor?"#"+anchor:"")
    </script>
    <meta http-equiv="refresh" content="0; url={url}">
</head>
<body>
Redirecting...
</body>
</html>
"""


def _write_cmap_redirects(site_dir: str) -> None:
    sd = Path(site_dir)
    for cmap_name, details in sorted(CATALOG.items(), key=lambda x: x[0].lower()):
        if "alias" in details:
            cmap_name = cmap_name.replace(":", "-")
            real = DocCmap(details["alias"])  # type: ignore
            old_path_abs = (
                sd / "catalog" / str(real.category) / cmap_name / "index.html"
            )
            old_path_abs.parent.mkdir(parents=True, exist_ok=True)
            content = REDIRECT_TEMPLATE.format(url=real.url())
            with open(old_path_abs, "w", encoding="utf-8") as f:
                f.write(content)


def on_post_build(config, **kwargs: Any) -> None:
    """Copy the extra javascripts to the output directory."""
    _write_cmap_redirects(config["site_dir"])
