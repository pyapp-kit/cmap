import json
from pathlib import Path

import mkdocs_gen_files
import numpy as np

from cmap import Colormap, _catalog
from cmap._util import report

TEMPLATE = """# {name}

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


def build_catalog(catalog: _catalog.Catalog) -> None:
    for name in catalog:
        if ":" not in name:
            continue
        try:
            info = catalog[name]
            category = info.category
            license_: str = info.license
        except KeyError as e:
            raise KeyError(f"Missing info for {name}: {e}") from e
        source = info.source
        source = f"[{source}]({source})" if source.startswith("http") else f"`{source}`"
        authors = ", ".join(info.authors)
        if license_ in LICENSE_URL:
            license_ = f"[{license_}]({LICENSE_URL[license_]})"

        # write data used for charts
        cm = Colormap(name)
        cmap_data = {
            k: np.around(v, 4).tolist() if isinstance(v, np.ndarray) else v
            for k, v in report(cm).items()
            if k in INCLUDE_DATA
        }

        # write the actual markdown file
        with mkdocs_gen_files.open(f"catalog/{category}/{name.lower()}.md", "w") as f:
            f.write(
                TEMPLATE.format(
                    name=name,
                    category=category.title(),
                    license=license_,
                    authors=authors,
                    source=source,
                    info=info.info,
                    data=json.dumps({name: cmap_data}, separators=(",", ":")),
                )
            )


build_catalog(_catalog.catalog)
