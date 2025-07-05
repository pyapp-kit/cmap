import json
from pathlib import Path
from typing import TYPE_CHECKING

import mkdocs_gen_files
import natsort
import numpy as np

if TYPE_CHECKING:
    from cmap import _catalog
from cmap import Colormap
from cmap._util import report_cvds

# TODO: convert to jinja
TEMPLATE = """# {name}

{aliases}

{info}

| category | license | authors | source |
| --- | --- | --- | --- |
| {category} | {license} | {authors} | {source} |

```python
from cmap import Colormap

cm = Colormap('{name}')  # case insensitive
```

{{{{ cmap: {name} 40 }}}}
{{{{ cmap_gray: {name} 30 }}}}
{{{{ cmap_sineramp: {name} }}}}

<form id="cvd" class="radio-group">
  <label class="radio-option" title="Full Vision">
    <input type="radio" name="cvd_button" value="normal" checked>
    <span class="material-icons">visibility</span>
    <span class="radio-label"> Normal Vision</span>
  </label>
  <label class="radio-option" title="Protanopic">
    <input type="radio" name="cvd_button" value="protan">
    <span class="material-icons">filter_1</span>
    <span class="radio-label"> Protanopic</span>
  </label>
  <label class="radio-option" title="Deuteranopic">
    <input type="radio" name="cvd_button" value="deutan">
    <span class="material-icons">filter_2</span>
    <span class="radio-label"> Deuteranopic</span>
  </label>
  <label class="radio-option" title="Tritananopic">
    <input type="radio" name="cvd_button" value="tritan">
    <span class="material-icons">filter_3</span>
    <span class="radio-label"> Tritanopic</span>
  </label>
</form>

## Perceptual Lightness

<canvas class="linearity-chart cmap-chart" data-cmap-name="{name}" width="800" height="350"></canvas>
<p style="text-align: center;">
<em style="font-size: small; color: gray;">
L* measured in
<a href="https://onlinelibrary.wiley.com/doi/10.1002/col.20227">CAM02 Uniform Color Space (CAM02-UCS)</a>
</em>
</p>

## RGB components

<canvas class="rgb-chart cmap-chart" data-cmap-name="{name}" width="800" height="350"></canvas>

## Hue & Saturation

<canvas class="hsl-chart cmap-chart" data-cmap-name="{name}" width="800" height="350"></canvas>


<script>
window.cmap_data = {data};

const cvd = document.getElementById("cvd");
cvd?.addEventListener("change", (e) => {{
    const selected = cvd.querySelector('input[name="cvd_button"]:checked')?.value;
    //window.cmap_data = {data}[selected];
    console.log("CVD type selected:", selected);
    // re-render the charts
    initCharts();
   
    console.log("Selected variant:", selected);
}});



<!-- Note: this is here because of `navigation.instant` in the mkdocs settings -->
typeof(initCharts) !== 'undefined' && initCharts();
</script>
"""

DOCS = Path(__file__).parent
LICENSE_URL = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "Apache-2.0": "https://www.apache.org/licenses/LICENSE-2.0",
    "MIT": "https://opensource.org/licenses/MIT",
    "BSD-3-Clause": "https://opensource.org/licenses/BSD-3-Clause",
    "BSD-2-Clause": "https://opensource.org/licenses/BSD-2-Clause",
    "PSF": "https://opensource.org/licenses/Python-2.0",
}


INCLUDE_DATA = (
    "x",
    "color",
    "R",
    "G",
    "B",
    "J",
    "lightness_derivs",
    "hue",
    "saturation",
    "chroma",
)


def build_catalog(catalog: "_catalog.Catalog") -> None:
    nav = mkdocs_gen_files.Nav()
    for name in natsort.natsorted(catalog, alg=natsort.ns.IGNORECASE):
        if ":" not in name:
            continue
        try:
            info = catalog[name]
            category = info.category
            license_: str = info.license
        except KeyError as e:
            raise KeyError(f"Missing info for {name}: {e}") from e

        # FIXME: not a great way to determine aliases...
        # prone to false positives if normalization is not perfect/consistent
        if info.qualified_name.lower() != name.lower():
            # skip aliases
            continue

        source = info.source
        source = f"[{source}]({source})" if source.startswith("http") else f"`{source}`"
        authors = ", ".join(info.authors)
        if license_ in LICENSE_URL:
            license_ = f"[{license_}]({LICENSE_URL[license_]})"

        # write data used for charts
        cm = Colormap(name)
        cmap_data = {
            cvd_type: {
                k: np.around(v, 4).tolist() if isinstance(v, np.ndarray) else v
                for k, v in report.items()
                if k in INCLUDE_DATA
            }
            for cvd_type, report in report_cvds(cm).items()
        }
        _aliases = [x for x in info.aliases if x != info.name]
        aliases = _make_aliases_md(_aliases) if _aliases else ""

        # write the actual markdown file
        doc_path = f"{category}/{name.lower()}.md"
        nav[(category.title(), name)] = doc_path
        with mkdocs_gen_files.open(f"catalog/{doc_path}", "w") as f:
            f.write(
                TEMPLATE.format(
                    name=name,
                    category=category.title(),
                    license=license_,
                    authors=authors,
                    source=source,
                    aliases=aliases,
                    info=info.info,
                    data=json.dumps({name: cmap_data}, separators=(",", ":")),
                )
            )

    # sort categories alphabetically
    nav._data = dict(sorted(nav._data.items(), key=lambda x: x[0][0]))
    with mkdocs_gen_files.open("catalog/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(["# SUMMARY { data-search-exclude }\n"])
        nav_file.writelines(nav.build_literate_nav())


def _make_aliases_md(aliases: list[str]) -> str:
    return "**Aliases**:  " + ", ".join(f"`{a}`" for a in aliases)


build_catalog(Colormap.catalog())
