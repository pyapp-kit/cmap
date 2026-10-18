---
render_macros: true
---

# Colormap Catalog

To use any colormap in the catalog, you can pass its name to the [`Colormap`][cmap.Colormap]
constructor:

```python
from cmap import Colormap

cmap = Colormap("viridis")
```

!!!note  "Coming from matplotlib?"
    We test against all of the named colormaps in matplotlib, so any `'name'`
    that you can use with `matplotlib.colormaps['name']` can also be passed to
    `cmap.Colormap`. To convert a `cmap.Colormap` to a native
    `matplotlib.colors.Colormap` instance, you may call
    [`.to_mpl()`][cmap.Colormap.to_matplotlib].

See [Colormaps](../colormaps.md#mapping-data-to-colors) for how to apply it to
your data, and the [Colormap API docs][cmap.Colormap] for details.

!!!tip "Tip: Reversed colormaps"

    You can append `'_r'` to any of the colormap names listed below to get a
    reversed version of that colormap. For example, `'viridis_r'`

    {{ cmap("viridis") }}
    {{ cmap("viridis_r") }}

    This works with function based colormaps as well:

    {{ cmap("cubehelix") }}
    {{ cmap("cubehelix_r") }}

## All colormaps

Filter by name, source, or lightness profile below, or
[compare colormaps side by side](../compare.md).

{{ cmap_catalog() }}
